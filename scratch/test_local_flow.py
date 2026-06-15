import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def make_post(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    print(f"POST {url} with {data}...")
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            body = res.read().decode()
            return res.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err_details = json.loads(body)
        except Exception:
            err_details = body
        return e.code, err_details
    except Exception as e:
        return 0, str(e)

def main():
    # Start the local FastAPI server if not running, or assume it's running
    email = "test_local_advisor@example.com"
    password = "SecurePassword123!"
    
    # Try to register
    reg_data = {
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": "Advisor",
        "company_name": "Local Diagnostic LLC"
    }
    status, res = make_post("/auth/register", reg_data)
    print(f"Status: {status}, Response: {res}")

if __name__ == "__main__":
    main()
