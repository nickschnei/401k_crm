import os
from pathlib import Path

def load_dotenv(env_path=".env"):
    """Parse a local .env file and load variables into os.environ if not already present."""
    path = Path(env_path)
    if not path.exists():
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    # Strip quotes around value
                    val = val.strip().strip("'").strip('"')
                    if key not in os.environ:
                        os.environ[key] = val
    except Exception as e:
        print(f"Warning: Could not read .env file: {e}")

# Automatically load environment variables on initialization
load_dotenv()

# App Core Settings
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///prospects.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "crm-default-secret-token")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
PORT = int(os.environ.get("PORT", "8000"))

# Authentication & Identity (Clerk)
CLERK_API_URL = os.environ.get("CLERK_API_URL", "https://api.clerk.com/v1")
CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY", "")
CLERK_JWT_VERIFICATION_KEY = os.environ.get("CLERK_JWT_VERIFICATION_KEY", "")

# Payment & Subscription Billing (Stripe)
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Contact Enrichment APIs
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")

# Storage & Parsing Directories
EXCEL_PROSPECT_FILE = os.environ.get("EXCEL_PROSPECT_FILE", "Combined 401k Prospecting Plan.xlsx")
DOL_DATA_DIR = os.environ.get("DOL_DATA_DIR", ".")
EXTRACTED_DATA_DIR = os.environ.get("EXTRACTED_DATA_DIR", "extracted_data")
