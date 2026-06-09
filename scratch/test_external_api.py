import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

eins = ["037966510", "130871985"]
api_key = "7c42774df07cf3e08e52708603a9731c"

for ein in eins:
    url = f"https://www.data-mining.co.uk/api/{api_key}/{ein}"
    print(f"Querying {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            data = response.read().decode('utf-8')
            print(f"Raw response: {data[:500]}")
    except Exception as e:
        print(f"Failed for EIN {ein}: {e}")
