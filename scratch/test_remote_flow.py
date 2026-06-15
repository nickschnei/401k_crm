import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://100.24.66.49/api/v1"

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

def make_get(endpoint, token=None):
    url = f"{BASE_URL}{endpoint}"
    print(f"GET {url}...")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
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
    email = "test_advisor_remote@example.com"
    password = "SecurePassword123!"
    
    # 1. Try to login
    status, res = make_post("/auth/login", {"email": email, "password": password})
    if status == 200:
        print("Login succeeded!")
        token = res["access_token"]
    else:
        print(f"Login failed: {res}. Attempting to register...")
        # 2. Try to register
        reg_data = {
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "Advisor",
            "company_name": "Remote Diagnostic LLC"
        }
        status, res = make_post("/auth/register", reg_data)
        if status == 201 or status == 200:
            print("Registration succeeded!")
            token = res["access_token"]
        else:
            print(f"Registration failed: {res}")
            sys.exit(1)
            
    print(f"Obtained Token: {token[:20]}...")
    
    # 3. Get profile details (/auth/me)
    status, me = make_get("/auth/me", token)
    print(f"User Profile: {me}")
    
    # 4. Get prospects
    status, prospects = make_get("/prospects/", token)
    print(f"Prospects count for tenant: {len(prospects) if isinstance(prospects, list) else 'Error'}")
    if isinstance(prospects, list):
        print(f"Prospects: {prospects[:2]}")
    else:
        print(f"Response: {prospects}")

if __name__ == "__main__":
    main()
