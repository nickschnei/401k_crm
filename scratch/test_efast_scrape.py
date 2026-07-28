import urllib.request
import ssl

url = "https://www.efast.dol.gov/portal/app/disseminate"
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=headers)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"Response length: {len(html)} bytes")
        print("URL after redirects:", resp.geturl())
        print(html[:1500])
except Exception as e:
    print("Error:", e)
