import os
import json
import time
import re
import urllib.parse
import http.client
from typing import Tuple, Optional, Dict

CACHE_FILE = os.path.join("extracted_data", "geocoding_cache.json")
ZIP_CACHE_FILE = os.path.join("extracted_data", "zip_cache.json")

# State centroids for US states as fallback coordinates to prevent route breakdown
STATE_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "ME": (45.2538, -69.4455),
    "IN": (39.7684, -86.1581),
    "NY": (43.0000, -75.0000),
    "MA": (42.4072, -71.3824),
    "NH": (43.1939, -71.5724),
    "VT": (44.0000, -72.6999),
    "CT": (41.6032, -72.7273),
    "RI": (41.5801, -71.4774),
    "NJ": (40.0583, -74.4057),
    "PA": (41.2033, -77.1945),
    "OH": (40.4173, -82.9071),
    "MI": (44.3148, -85.6024),
    "IL": (40.6331, -89.3985),
    "WI": (43.7844, -88.7879),
    "CA": (36.7783, -119.4179),
    "TX": (31.9686, -99.9018),
    "FL": (27.6648, -81.5158),
}

def load_json_cache(filepath: str) -> dict:
    if not os.path.exists(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json_cache(filepath: str, cache: dict):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving cache file {filepath}: {e}")

# Global cache dictionaries loaded once
_cache = load_json_cache(CACHE_FILE)
_zip_cache = load_json_cache(ZIP_CACHE_FILE)

def extract_5digit_zip(address_str: str) -> Optional[str]:
    """
    Extracts and normalizes a 5-digit ZIP code from an address string.
    Supports floats converted to strings (e.g. '4843.0' -> '04843') and normal text.
    """
    cleaned = address_str.strip()
    if cleaned.endswith(".0"):
        cleaned = cleaned[:-2]
        
    # Look for 5-digit zip patterns
    match = re.search(r"\b\d{5}\b", cleaned)
    if match:
        return match.group(0)
        
    # Look for 4-digit zip pattern that needs a leading zero (e.g. Maine zips like '4843' -> '04843')
    match_4 = re.search(r"\b\d{4}\b", cleaned)
    if match_4:
        return match_4.group(0).zfill(5)
        
    # Standard numbers-only check if the string itself is just a ZIP code code
    digits = "".join(c for c in cleaned if c.isdigit())
    if len(digits) >= 4:
        return digits[:5].zfill(5)
        
    return None

def geocode_zip_zippopotam(zip_code: str) -> Optional[Tuple[float, float]]:
    """
    Geocodes a US ZIP code instantly using Zippopotam.us API.
    Does not require API keys or rate-limiting delays.
    """
    global _zip_cache
    if zip_code in _zip_cache:
        return tuple(_zip_cache[zip_code])
        
    print(f"[Geocoder] Querying Zippopotam for ZIP: {zip_code}")
    host = "api.zippopotam.us"
    path = f"/us/{zip_code}"
    
    try:
        # HTTP client connection (Zippopotam supports standard HTTP/HTTPS quickly)
        conn = http.client.HTTPConnection(host, timeout=5)
        conn.request("GET", path)
        res = conn.getresponse()
        
        if res.status == 200:
            data = json.loads(res.read().decode("utf-8"))
            if data and "places" in data and len(data["places"]) > 0:
                place = data["places"][0]
                lat = float(place["latitude"])
                lon = float(place["longitude"])
                print(f"[Geocoder] ZIP success: {lat}, {lon}")
                
                # Cache results
                _zip_cache[zip_code] = [lat, lon]
                save_json_cache(ZIP_CACHE_FILE, _zip_cache)
                return lat, lon
    except Exception as e:
        print(f"[Geocoder] Zippopotam connection error for {zip_code}: {e}")
        
    return None

def get_state_fallback(address_str: str) -> Tuple[float, float]:
    """
    Returns fallback coordinates based on US state letters found in the address.
    """
    addr_upper = address_str.upper()
    for state, coords in STATE_CENTROIDS.items():
        if f" {state} " in addr_upper or addr_upper.endswith(f" {state}") or f", {state}" in addr_upper:
            import random
            offset_lat = random.uniform(-0.1, 0.1)
            offset_lon = random.uniform(-0.1, 0.1)
            return coords[0] + offset_lat, coords[1] + offset_lon
            
    # Default fall back (Lewiston, ME area)
    import random
    return 44.1003 + random.uniform(-0.03, 0.03), -70.2147 + random.uniform(-0.03, 0.03)

def geocode_address(address_str: str) -> Tuple[float, float]:
    """
    Geocodes an address string. First attempts an instant ZIP code lookup (Zippopotam),
    falling back to Nominatim (OpenStreetMap) if no ZIP is found or the ZIP query fails.
    """
    global _cache
    sanitized_address = address_str.strip().replace("\n", ", ")
    
    # 1. Check full address cache first
    if sanitized_address in _cache:
        return tuple(_cache[sanitized_address])
        
    # 2. Extract and attempt instant ZIP geocoding
    zip_code = extract_5digit_zip(sanitized_address)
    if zip_code:
        zip_coords = geocode_zip_zippopotam(zip_code)
        if zip_coords:
            # Save to full address cache to avoid future ZIP extraction parses
            _cache[sanitized_address] = list(zip_coords)
            save_json_cache(CACHE_FILE, _cache)
            return zip_coords
            
    # 3. Fallback: Query Nominatim if ZIP lookup is not possible/fails
    headers = {"User-Agent": "401k-CRM-Trip-Planner/1.0 (nickschnei/401k_crm)"}
    host = "nominatim.openstreetmap.org"
    encoded_addr = urllib.parse.quote(sanitized_address)
    path = f"/search?q={encoded_addr}&format=json&limit=1"
    
    print(f"[Geocoder] Falling back to Nominatim for: {sanitized_address}")
    
    # Sleep 1.1s for rate limit safety before Nominatim requests
    time.sleep(1.1)
    
    try:
        conn = http.client.HTTPSConnection(host, timeout=5)
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        
        if res.status == 200:
            data = json.loads(res.read().decode("utf-8"))
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                print(f"[Geocoder] Nominatim Success! Coords: {lat}, {lon}")
                
                # Cache results
                _cache[sanitized_address] = [lat, lon]
                save_json_cache(CACHE_FILE, _cache)
                return lat, lon
    except Exception as e:
        print(f"[Geocoder] Nominatim connection error for {sanitized_address}: {e}")
        
    # 4. Fallback to state centroids
    fallback_coords = get_state_fallback(sanitized_address)
    _cache[sanitized_address] = list(fallback_coords)
    save_json_cache(CACHE_FILE, _cache)
    return fallback_coords
