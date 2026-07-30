from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
import config
from utils.auth import ClerkUser, get_current_user
from utils.pii import screen_and_mask_pii

# Database imports
from api.database import SessionLocal
from api.models import Prospect, Form5500Audit
from sqlalchemy import and_, or_
import json

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str

# ---------------------------------------------------------
# Database Query Tools for the Gemini Agent
# ---------------------------------------------------------

def search_prospects(
    industry: str = None,
    provider: str = None,
    state: str = None,
    min_assets: float = None,
    max_assets: float = None,
    min_participants: int = None,
    compliance_failed: bool = None,
    limit: int = 10
) -> str:
    """
    Search and identify 401(k) plan sponsors (prospects) in the database based on filters.
    Use this to identify target companies, find Vanguard/Fidelity plans, or find plans in specific states/industries.
    """
    db = SessionLocal()
    try:
        query = db.query(Prospect, Form5500Audit).outerjoin(Form5500Audit, Prospect.ein == Form5500Audit.ein)
        
        filters = []
        if industry:
            filters.append(Prospect.industry.ilike(f"%{industry}%"))
        if provider:
            filters.append(Prospect.provider.ilike(f"%{provider}%"))
        if min_assets is not None:
            filters.append(Prospect.total_assets >= min_assets)
        if max_assets is not None:
            filters.append(Prospect.total_assets <= max_assets)
        if min_participants is not None:
            filters.append(Prospect.active_participants >= min_participants)
        if state:
            filters.append(Form5500Audit.dol_state.ilike(state))
        if compliance_failed is not None:
            filters.append(Form5500Audit.compliance_failed == compliance_failed)
            
        if filters:
            query = query.filter(and_(*filters))
            
        query = query.order_by(Prospect.total_assets.desc()).limit(limit)
        
        results = []
        for p, a in query.all():
            results.append({
                "ein": p.ein,
                "employer_name": p.employer_name,
                "industry": p.industry,
                "provider": p.provider,
                "total_assets": float(p.total_assets) if p.total_assets else 0.0,
                "active_participants": p.active_participants,
                "status": p.status,
                "state": a.dol_state if a else None,
                "compliance_failed": a.compliance_failed if a else False,
                "fee_red_flag": a.fee_red_flag if a else False,
                "participation_red_flag": a.participation_red_flag if a else False,
            })
            
        if not results:
            return "No prospects matching the criteria were found in the database."
            
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error querying database: {str(e)}"
    finally:
        db.close()

def get_compliance_report(ein: str) -> str:
    """
    Get the detailed fiduciary health and compliance audit report for a company by its 9-digit EIN.
    Exposes compliance failure status, fee ratio, participation rates, and admin expenses.
    """
    db = SessionLocal()
    try:
        normalized_ein = "".join(c for c in ein if c.isdigit())
        audit = db.query(Form5500Audit).filter(Form5500Audit.ein == normalized_ein).first()
        if not audit:
            return f"No compliance report found for EIN: {ein}"
            
        report = {
            "ein": audit.ein,
            "employer_name": audit.employer_name,
            "plan_name": audit.plan_name,
            "total_assets": float(audit.total_assets) if audit.total_assets else 0.0,
            "active_participants": audit.active_participants,
            "total_eligible_employees": audit.total_eligible_employees,
            "participation_rate": float(audit.participation_rate) if audit.participation_rate else 0.0,
            "admin_expenses": float(audit.admin_expenses) if audit.admin_expenses else 0.0,
            "corrective_distributions": float(audit.corrective_distributions) if audit.corrective_distributions else 0.0,
            "fee_ratio": float(audit.fee_ratio) if audit.fee_ratio else 0.0,
            "compliance_failed": audit.compliance_failed,
            "fee_red_flag": audit.fee_red_flag,
            "participation_red_flag": audit.participation_red_flag,
            "administrator_name": audit.administrator_name,
            "address": f"{audit.dol_address}, {audit.dol_city}, {audit.dol_state} {audit.dol_zip}"
        }
        return json.dumps(report, indent=2)
    except Exception as e:
        return f"Error retrieving compliance report: {str(e)}"
    finally:
        db.close()

def get_contact_info(ein: str) -> str:
    """
    Get the decision maker contact information (name, email, phone, notes) for a prospect by its 9-digit EIN.
    """
    db = SessionLocal()
    try:
        normalized_ein = "".join(c for c in ein if c.isdigit())
        prospect = db.query(Prospect).filter(Prospect.ein == normalized_ein).first()
        if not prospect:
            return f"No prospect found with EIN: {ein}"
            
        contact = {
            "ein": prospect.ein,
            "employer_name": prospect.employer_name,
            "contact_name": prospect.contact_name,
            "contact_email": prospect.contact_email,
            "contact_phone": prospect.contact_phone,
            "status": prospect.status,
            "notes": prospect.notes
        }
        return json.dumps(contact, indent=2)
    except Exception as e:
        return f"Error retrieving contact info: {str(e)}"
    finally:
        db.close()

# ---------------------------------------------------------
# Agent Service Logic
# ---------------------------------------------------------

def get_genai_client():
    api_key = config.GOOGLE_GENAI_API_KEY
    if not api_key:
        import os
        api_key = os.environ.get("GEMINI_API_KEY", "")
    
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Google GenAI API Key is not configured. Please set GOOGLE_GENAI_API_KEY in your .env file."
        )
    return genai.Client(api_key=api_key)

async def stream_gemini_response(prompt: str):
    """
    Asynchronously resolve tool calls on the local database first, then stream the final
    ERISA copilot response to the client with automatic model fallback to avoid 503 errors.
    """
    try:
        client = get_genai_client()
        
        system_instruction = (
            "You are an expert 401(k) Fiduciary Plan Analyst and ERISA Compliance Consultant. "
            "You have direct access to the CRM's local database of 401(k) prospects and Form 5500 audits. "
            "Your goal is to help advisors analyze plan sponsors, identify specific areas of improvement, "
            "and build compelling prospecting cases.\n\n"
            "When asked to analyze a company or a plan, or to find areas of improvement, you MUST follow this Fiduciary Analysis Checklist:\n"
            "1. Retrieve the company's records using `search_prospects` and get the compliance audit details using `get_compliance_report`.\n"
            "2. Analyze Fees (Fee Ratio):\n"
            "   - If fee_ratio is high (e.g. > 0.0080 or 80 bps) or fee_red_flag is True, highlight that they are overpaying. "
            "Compare it with standard benchmarks (typically 40-60 bps). Recommend provider fee benchmarking or migrating to lower-cost institutional share classes.\n"
            "3. Analyze Participant Engagement (Participation Rate):\n"
            "   - If participation_rate is low (e.g. < 75%) or participation_red_flag is True, recommend plan design improvements "
            "such as implementing automatic enrollment (auto-enrollment), automatic escalation (auto-escalation), or optimizing the employer matching thresholds.\n"
            "4. Analyze IRS Non-Discrimination Testing (Corrective Distributions):\n"
            "   - If corrective_distributions > 0, highlight the exact dollar amount returned to highly compensated employees (HCEs). "
            "Explain that this indicates failed ADP/ACP non-discrimination testing. "
            "Recommend adopting a Safe Harbor plan design (e.g. 3% safe harbor non-elective or matching) to bypass ADP/ACP testing entirely and eliminate corrective refunds.\n"
            "5. Analyze Compliance Failures (compliance_failed):\n"
            "   - If compliance_failed is True, highlight this as a critical fiduciary liability risk. Recommend a full fiduciary checkup.\n\n"
            "FORMAT YOUR RESPONSE PROFESSIONALLY:\n"
            "- Start with an Executive Summary of the plan (assets, active participants, provider).\n"
            "- List 'Key Findings & Fiduciary Weaknesses' using exact figures from the database.\n"
            "- Provide a 'Concrete Fiduciary Recommendations' section with action items (Safe Harbor design, fee negotiation, auto-enrollment) based on the data.\n"
            "- Maintain an objective, expert consultant tone. Decline explicit personal tax or investment advice."
        )
        
        tools = [search_prospects, get_compliance_report, get_contact_info]
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
        
        # Primary and fallback models
        fallback_models = ['gemini-3.5-flash', 'gemini-2.5-flash']
        active_model = 'gemini-3.5-flash'
        
        # Tool execution loop
        for _ in range(5):
            response = None
            last_err = None
            
            # Try calling models in order of priority
            for model_name in fallback_models:
                try:
                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            tools=tools,
                            temperature=0.2,
                        )
                    )
                    active_model = model_name  # Keep using this model if successful
                    break
                except Exception as e:
                    last_err = e
                    print(f"[Agent Model Fallback] Model {model_name} generate failed: {str(e)}. Trying next...")
                    continue
            
            if response is None:
                raise last_err if last_err else Exception("No active Gemini models responded.")
            
            # Process function calls
            if response.function_calls:
                contents.append(response.candidates[0].content)
                
                tool_response_parts = []
                for function_call in response.function_calls:
                    name = function_call.name
                    args = function_call.args or {}
                    
                    print(f"[Agent Tool Call] Executing: {name} with args {args}")
                    
                    if name == "search_prospects":
                        result = search_prospects(
                            industry=args.get("industry"),
                            provider=args.get("provider"),
                            state=args.get("state"),
                            min_assets=float(args["min_assets"]) if args.get("min_assets") is not None else None,
                            max_assets=float(args["max_assets"]) if args.get("max_assets") is not None else None,
                            min_participants=int(args["min_participants"]) if args.get("min_participants") is not None else None,
                            compliance_failed=bool(args["compliance_failed"]) if args.get("compliance_failed") is not None else None,
                            limit=int(args.get("limit", 10))
                        )
                    elif name == "get_compliance_report":
                        result = get_compliance_report(ein=str(args.get("ein")))
                    elif name == "get_contact_info":
                        result = get_contact_info(ein=str(args.get("ein")))
                    else:
                        result = f"Error: Tool {name} not found."
                        
                    tool_response_parts.append(
                        types.Part.from_function_response(
                            name=name,
                            response={"result": result}
                        )
                    )
                
                contents.append(types.Content(role="user", parts=tool_response_parts))
                continue
            else:
                # No function calls, stream the final response text
                response_stream = None
                last_stream_err = None
                
                # Order models starting with the successful active model
                stream_models = [active_model] + [m for m in fallback_models if m != active_model]
                
                for model_name in stream_models:
                    try:
                        response_stream = await client.aio.models.generate_content_stream(
                            model=model_name,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                tools=tools,
                                temperature=0.2,
                            )
                        )
                        async for chunk in response_stream:
                            if chunk.text:
                                yield chunk.text
                        return
                    except Exception as e:
                        last_stream_err = e
                        print(f"[Agent Stream Fallback] Model {model_name} stream failed: {str(e)}. Trying next...")
                        continue
                
                if response_stream is None:
                    raise last_stream_err if last_stream_err else Exception("No active Gemini model streams responded.")
                
    except Exception as e:
        yield f"\n[Error streaming from Copilot: {str(e)}]"

@router.post("/chat")
async def chat_agent(
    request: ChatRequest,
    current_user: ClerkUser = Depends(get_current_user)
):
    """
    Streaming chat endpoint that processes the prompt, runs PII screening,
    resolves database tool calls, and streams the response chunks back in real-time.
    """
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    # 1. Run PII Screening Utility
    masked_prompt, detected_pii = screen_and_mask_pii(prompt)
    
    if detected_pii:
        pii_types = ", ".join(detected_pii)
        raise HTTPException(
            status_code=400,
            detail=f"PII screening violation: Plain text {pii_types} detected and blocked."
        )
    
    # 2. Return streaming response
    return StreamingResponse(
        stream_gemini_response(masked_prompt),
        media_type="text/plain"
    )

# ---------------------------------------------------------
# Item 3: AI Outreach Assistant & Note Summarization Endpoints
# ---------------------------------------------------------

class SummarizeNotesRequest(BaseModel):
    raw_notes: str
    contact_name: Optional[str] = None
    employer_name: Optional[str] = None

class SummarizeNotesResponse(BaseModel):
    polished_notes: str
    key_takeaways: list[str]
    suggested_followup_days: Optional[int] = 3
    suggested_followup_note: Optional[str] = "Follow up on fiduciary diagnostic review"

class GenerateEmailRequest(BaseModel):
    interaction_type: str
    notes: str
    contact_name: Optional[str] = None
    employer_name: Optional[str] = None

class GenerateEmailResponse(BaseModel):
    subject: str
    body: str

class NextActionRequest(BaseModel):
    ein: str

class NextActionResponse(BaseModel):
    recommended_action: str
    reasoning: str
    urgency: str

@router.post("/summarize-notes", response_model=SummarizeNotesResponse)
async def summarize_notes(
    request: SummarizeNotesRequest,
    current_user: ClerkUser = Depends(get_current_user)
):
    """
    Format raw, unstructured call/meeting notes into clean executive takeaways,
    and automatically extract follow-up action items.
    """
    raw = request.raw_notes.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Notes content cannot be empty.")

    contact = request.contact_name or "Contact"
    company = request.employer_name or "Prospect Organization"

    # Attempt Gemini API call if key is configured
    api_key = getattr(config, "GEMINI_API_KEY", None)
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt_text = f"""You are an executive 401(k) fiduciary sales assistant. Clean up and format the following raw notes from a meeting/call with {contact} at {company}.
Raw notes: "{raw}"

Return JSON matching this schema:
{{
  "polished_notes": "Clean, formatted paragraph summarizing the interaction.",
  "key_takeaways": ["Takeaway 1", "Takeaway 2"],
  "suggested_followup_days": 3,
  "suggested_followup_note": "Short task description for follow-up"
}}
Return ONLY valid JSON."""
            
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_text
            )
            text_resp = response.text or ""
            if "```json" in text_resp:
                text_resp = text_resp.split("```json")[1].split("```")[0].strip()
            elif "```" in text_resp:
                text_resp = text_resp.split("```")[1].strip()
            
            data = json.loads(text_resp)
            return SummarizeNotesResponse(
                polished_notes=data.get("polished_notes", raw),
                key_takeaways=data.get("key_takeaways", ["Discussed plan fees and fiduciary oversight"]),
                suggested_followup_days=data.get("suggested_followup_days", 3),
                suggested_followup_note=data.get("suggested_followup_note", "Send fiduciary benchmarking proposal")
            )
        except Exception as err:
            print(f"[AISummarize] Gemini call notice: {err}. Falling back to structured heuristic formatter.")

    # Fallback heuristic cleanup logic
    lines = [line.strip("-•* ").capitalize() for line in raw.split("\n") if line.strip()]
    takeaways = lines if len(lines) > 0 else ["Reviewed current 401(k) plan structure and fee schedule"]
    polished = f"Interaction with {contact} ({company}): " + ". ".join(lines)
    if not polished.endswith("."):
        polished += "."

    return SummarizeNotesResponse(
        polished_notes=polished,
        key_takeaways=takeaways[:4],
        suggested_followup_days=3,
        suggested_followup_note=f"Follow up with {contact} regarding fee benchmarking proposal"
    )

@router.post("/generate-followup-email", response_model=GenerateEmailResponse)
async def generate_followup_email(
    request: GenerateEmailRequest,
    current_user: ClerkUser = Depends(get_current_user)
):
    """
    Generate a polished, personalized post-call or post-meeting follow-up email draft.
    """
    notes = request.notes.strip()
    contact = request.contact_name or "Plan Sponsor"
    company = request.employer_name or "your organization"

    api_key = getattr(config, "GEMINI_API_KEY", None)
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt_text = f"""Draft a professional follow-up email after a {request.interaction_type} with {contact} at {company}.
Discussion notes: "{notes}"

Return ONLY valid JSON matching this schema:
{{
  "subject": "Email Subject Line",
  "body": "Full body text of the email..."
}}"""
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_text
            )
            text_resp = response.text or ""
            if "```json" in text_resp:
                text_resp = text_resp.split("```json")[1].split("```")[0].strip()
            elif "```" in text_resp:
                text_resp = text_resp.split("```")[1].strip()
                
            data = json.loads(text_resp)
            return GenerateEmailResponse(
                subject=data.get("subject", f"Following Up — {company} 401(k) Plan Review"),
                body=data.get("body", "")
            )
        except Exception as err:
            print(f"[AIEmail] Gemini call notice: {err}. Using rule-based generator.")

    subject = f"Thank you for your time — {company} 401(k) Fiduciary Follow-up"
    body = f"""Dear {contact},

Thank you for taking the time to speak today regarding the {company} 401(k) retirement plan.

Based on our discussion:
{notes}

As discussed, I am preparing a side-by-side fiduciary diagnostic report comparing your plan's fee structure and investment menu against industry benchmarks.

Please let me know if next Tuesday or Thursday works best for a brief 15-minute review of our findings.

Best regards,

[Your Name]
Fiduciary Advisory Services
"""
    return GenerateEmailResponse(subject=subject, body=body)

@router.post("/next-action", response_model=NextActionResponse)
async def recommend_next_action(
    request: NextActionRequest,
    current_user: ClerkUser = Depends(get_current_user)
):
    """
    Evaluate prospect audit flags and interaction logs to recommend the next best sales action.
    """
    clean_ein = "".join(c for c in str(request.ein) if c.isdigit()).zfill(9)
    db = SessionLocal()
    try:
        prospect = db.query(Prospect).filter(Prospect.ein == clean_ein).first()
        audit = db.query(Form5500Audit).filter(Form5500Audit.ein == clean_ein).first()
        
        has_fee_flag = bool(audit and audit.fee_red_flag)
        has_part_flag = bool(audit and audit.participation_red_flag)
        has_compliance_flag = bool(audit and audit.compliance_failed)
        
        if has_fee_flag and has_compliance_flag:
            return NextActionResponse(
                recommended_action="Schedule Urgent Fee & Compliance Review",
                reasoning="Plan exhibits both high fee ratio drag (>60bps) and historic compliance testing failures. Immediate opportunity for fiduciary risk mitigation.",
                urgency="High"
            )
        elif has_fee_flag:
            return NextActionResponse(
                recommended_action="Present Fee Benchmarking & Vendor Compression Audit",
                reasoning="Administrative fee ratio exceeds peer benchmarks. Pitch vendor fee negotiation to reduce drag on employee savings.",
                urgency="High"
            )
        elif has_part_flag:
            return NextActionResponse(
                recommended_action="Propose Auto-Enrollment & Plan Design Modernization",
                reasoning="Employee participation rate is below 70%. Focus on automated enrollment designs and employee financial wellness tools.",
                urgency="Medium"
            )
        else:
            return NextActionResponse(
                recommended_action="Conduct Annual Fiduciary Structural Check",
                reasoning="Plan metrics align with general guidelines. Propose a periodic fiduciary checkup to ensure continued fee competitiveness as assets scale.",
                urgency="Low"
            )
    finally:
        db.close()

