import urllib.request
import ssl

url = "http://100.24.66.49/api/v1/audits/batch/zip?eins=188021660,028353551"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    print(f"Testing GET {url}...")
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        data = resp.read()
        print(f"STATUS: {resp.status}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}")
        print(f"Downloaded ZIP size: {len(data)} bytes")
        print("SUCCESS! Batch ZIP generated and downloaded cleanly.")
except Exception as e:
    print(f"ERROR: {e}")
