import urllib.request
import json
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

eins = ["020444227", "987523523"]

for ein in eins:
    url = f"http://127.0.0.1:8000/api/v1/audits/{ein}"
    print(f"Requesting {url}...")
    start_time = time.time()
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            data = response.read().decode('utf-8')
            parsed = json.loads(data)
            duration = time.time() - start_time
            print(f"Success for EIN {ein} in {duration:.4f} seconds!")
            print(json.dumps(parsed, indent=2))
    except Exception as e:
        duration = time.time() - start_time
        print(f"Failed for EIN {ein} in {duration:.4f} seconds: {e}")
