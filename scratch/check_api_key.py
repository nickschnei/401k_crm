import os
import sys

# Ensure config can be imported
sys.path.append("/app")

import config
from google import genai

print("=== CHECKING API KEY CONFIG ===")
api_key = config.GOOGLE_GENAI_API_KEY
print(f"GOOGLE_GENAI_API_KEY length: {len(api_key) if api_key else 0}")
if api_key:
    print(f"GOOGLE_GENAI_API_KEY starts with: {api_key[:8]}...")
else:
    print("GOOGLE_GENAI_API_KEY is not set.")

gemini_key = os.environ.get("GEMINI_API_KEY", "")
print(f"GEMINI_API_KEY length: {len(gemini_key) if gemini_key else 0}")

print("\n=== TRYING GEMINI CALL ===")
try:
    active_key = api_key or gemini_key
    if not active_key:
        print("Error: No active API key found in config or environment.")
    else:
        client = genai.Client(api_key=active_key)
        for model in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-3.5-flash"]:
            try:
                print(f"Calling model: {model}...")
                response = client.models.generate_content(
                    model=model,
                    contents="Hello",
                )
                print(f"SUCCESS with {model}: {response.text[:30].strip()}...")
            except Exception as e:
                print(f"FAILED with {model}: {str(e)}")
except Exception as e:
    print(f"Client initialization failed: {str(e)}")
