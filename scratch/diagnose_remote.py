import urllib.request
import urllib.error
import json
import sys

def probe(url):
    print(f"Probing {url}...")
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"  Status: {response.status}")
            print(f"  Headers: {dict(response.info())}")
            body = response.read().decode()
            print(f"  Body length: {len(body)}")
            print(f"  Body (first 200 chars): {body[:200]}")
    except urllib.error.HTTPError as e:
        print(f"  HTTPError: {e.code} - {e.reason}")
        print(f"  Headers: {dict(e.headers)}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    print("--- Probing Port 80 (Caddy Proxy) ---")
    probe("http://100.24.66.49/api/v1/discovery/sync/status")
    probe("http://100.24.66.49/")
    
    print("\n--- Probing Port 8000 (FastAPI Backend) ---")
    probe("http://100.24.66.49:8000/api/v1/discovery/sync/status")
    
    print("\n--- Probing Port 3000 (NextJS Frontend) ---")
    probe("http://100.24.66.49:3000/")
