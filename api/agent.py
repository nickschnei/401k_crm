from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
import config
from utils.auth import ClerkUser, get_current_user
from utils.pii import screen_and_mask_pii

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str

# Initialize the Gemini client using the official google-genai SDK
# If key is empty, it will fall back to reading GEMINI_API_KEY environment variable.
# We initialize it inside a function or check it dynamically to avoid startup failures if keys are missing.
def get_genai_client():
    api_key = config.GOOGLE_GENAI_API_KEY
    if not api_key:
        # Fallback to check if GEMINI_API_KEY is present in environment
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
    Asynchronously stream text chunks from gemini-3.5-flash with compliance copilot configurations.
    """
    try:
        client = get_genai_client()
        
        system_instruction = (
            "You are an enterprise 401(k) and ERISA compliance copilot. "
            "You must remain objective, never hallucinate compliance dates or vesting equations, "
            "and strictly decline to give explicit personal tax or investment advice. "
            "Always state compliance facts clearly and reference official IRS/DOL sources where appropriate."
        )
        
        # Call the streaming endpoint using client.aio for async
        response_stream = await client.aio.models.generate_content_stream(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )
        )
        
        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"\n[Error streaming from Copilot: {str(e)}]"

@router.post("/chat")
async def chat_agent(
    request: ChatRequest,
    current_user: ClerkUser = Depends(get_current_user)
):
    """
    Streaming chat endpoint that processes the prompt, runs PII screening,
    and streams the response chunks back in real-time.
    """
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    # 1. Run PII Screening Utility
    masked_prompt, detected_pii = screen_and_mask_pii(prompt)
    
    # If PII is detected, we block the request and return an error message
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
