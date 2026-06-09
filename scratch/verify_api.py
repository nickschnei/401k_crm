import urllib.request
import json

try:
    # 1. Health check
    response = urllib.request.urlopen("http://localhost:8000/health")
    health = json.loads(response.read().decode('utf-8'))
    print("API Health Check:", health)
    
    # 2. Lazy audit fallback check (EIN 188021660 which is missing from DOL but in Excel)
    print("\nVerifying lazy-audit fallback for EIN 188021660:")
    response = urllib.request.urlopen("http://localhost:8000/api/v1/audits/188021660")
    audit = json.loads(response.read().decode('utf-8'))
    print("- Found status:", audit.get("found"))
    print("- Assets:", audit.get("total_assets"))
    print("- Schedule:", audit.get("schedule_type"))
    print("- Active Participants:", audit.get("active_participants"))
    
    # 3. Discovery search check
    print("\nVerifying discovery search:")
    # Search for an employer name in DOL filing table
    response = urllib.request.urlopen("http://localhost:8000/api/v1/discovery/?search=Kirkpatrick")
    discovery = json.loads(response.read().decode('utf-8'))
    print(f"- Matches found: {len(discovery)}")
    if discovery:
        print("- First match details:")
        print(f"  Employer: {discovery[0]['employer_name']}")
        print(f"  Plan: {discovery[0]['plan_name']}")
        print(f"  Assets: {discovery[0]['total_assets']}")
        print(f"  Participants: {discovery[0]['participants']}")
        print(f"  EIN: {discovery[0]['ein']}")
        
except Exception as e:
    print("Verification failed:", e)
