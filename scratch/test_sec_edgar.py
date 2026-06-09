import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Apple's CIK is 0000320193
cik = "0000320193"
url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
print(f"Querying {url}...")

# SEC EDGAR requires a custom User-Agent identifying the client
headers = {
    'User-Agent': 'Antigravity401kCRM/1.0 (nickschneider17@gmail.com)'
}
req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
        data = response.read().decode('utf-8')
        parsed = json.loads(data)
        print("Successfully loaded Apple submissions!")
        print(f"Company Name: {parsed.get('name')}")
        print(f"EIN: {parsed.get('ein')}")
        
        # Look for 11-K filings
        filings = parsed.get('filings', {}).get('recent', {})
        forms = filings.get('form', [])
        
        found_11k = []
        for idx, form in enumerate(forms):
            if form == '11-K':
                accession = filings.get('accessionNumber', [])[idx]
                doc_name = filings.get('primaryDocument', [])[idx]
                filing_date = filings.get('filingDate', [])[idx]
                found_11k.append({
                    "accession": accession,
                    "doc_name": doc_name,
                    "filing_date": filing_date
                })
        print(f"Found 11-K filings: {found_11k}")
except Exception as e:
    print(f"Error: {e}")
