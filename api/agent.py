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
            
        # Order by assets desc
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
        # Strip non-digits
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
    ERISA copilot response to the client.
    """
    try:
        client = get_genai_client()
        
        system_instruction = (
            "You are an enterprise 401(k) and ERISA compliance copilot. "
            "You have direct access to the CRM's local database of plans, prospects, and compliance audits. "
            "Whenever a user asks to search for companies, list prospects, find plans (e.g. by provider, size, state, or industry), "
            "retrieve contact info, or check audit compliance and red flags, you MUST use the database query tools to fetch the actual details. "
            "Always output specific figures, names, and red flags returned by the tools. "
            "Do not state generic summaries if specific database records are available. "
            "You must remain objective, never hallucinate compliance dates or vesting equations, "
            "and strictly decline to give explicit personal tax or investment advice."
        )
        
        # Define the tools list
        tools = [search_prospects, get_compliance_report, get_contact_info]
        
        # Build contents message list
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
        
        # Tool execution loop (max 5 iterations to prevent infinite loops)
        for _ in range(5):
            response = await client.aio.models.generate_content(
                model='gemini-3.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tools,
                    temperature=0.2,
                )
            )
            
            # Check if model requested any function calls
            if response.function_calls:
                # Append the model content containing the function call(s)
                contents.append(response.candidates[0].content)
                
                # Execute the tool calls
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
                        
                    # Format function response part
                    tool_response_parts.append(
                        types.Part.from_function_response(
                            name=name,
                            response={"result": result}
                        )
                    )
                
                # Append function responses as role="user" content
                contents.append(types.Content(role="user", parts=tool_response_parts))
                
                # Loop back to let the model generate text or another call
                continue
            else:
                # No function calls. We can stream the final generated response text
                response_stream = await client.aio.models.generate_content_stream(
                    model='gemini-3.5-flash',
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
