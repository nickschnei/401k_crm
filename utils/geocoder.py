import os
import json
import time
import urllib.parse
import http.client
from typing import Tuple, Optional, Dict

CACHE_FILE = os.path.join("extracted_data", "geocoding_cache.json")

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

def load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_cache(cache: dict):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving geocoding cache: {e}")

# Global cache dictionary loaded once
_cache = load_cache()

def get_state_fallback(address_str: str) -> Tuple[float, float]:
    """
    Returns fallback coordinates based on US state letters found in the address.
    Defaults to Lewiston, ME coordinates if no state matches.
    """
    addr_upper = address_str.upper()
    for state, coords in STATE_CENTROIDS.items():
        if f" {state} " in addr_upper or addr_upper.endswith(f" {state}") or f", {state}" in addr_upper:
            # Shift slightly to avoid all fallback markers stacking on the exact same pixel
            import random
            offset_lat = random.uniform(-0.15, 0.15)
            offset_lon = random.uniform(-0.15, 0.15)
            return coords[0] + offset_lat, coords[1] + offset_lon
            
    # Default fall back (Lewiston, ME center area)
    import random
    return 44.1003 + random.uniform(-0.05, 0.05), -70.2147 + random.uniform(-0.05, 0.05)

def geocode_address(address_str: str) -> Tuple[float, float]:
    """
    Geocodes an address string using Nominatim OpenStreetMap API with rate limit safety.
    Returns (lat, lon) coordinates, fallback values if geocoding fails.
    """
    global _cache
    sanitized_address = address_str.strip().replace("\n", ", ")
    
    # 1. Check cache first
    if sanitized_address in _cache:
        return tuple(_cache[sanitized_address])
        
    # 2. Call Nominatim
    # Nominatim Usage Policy requires a valid User-Agent
    headers = {"User-Agent": "401k-CRM-Trip-Planner/1.0 (nickschnei/401k_crm)"}
    host = "nominatim.openstreetmap.org"
    encoded_addr = urllib.parse.quote(sanitized_address)
    path = f"/search?q={encoded_addr}&format=json&limit=1"
    
    print(f"[Geocoder] Querying Nominatim for: {sanitized_address}")
    
    # Respect rate-limit: Sleep 1.1s before request to avoid blocking
    time.sleep(1.1)
    
    try:
        conn = http.client.HTTPSConnection(host, timeout=8)
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        
        if res.status == 200:
            data = json.loads(res.read().decode("utf-8"))
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                print(f"[Geocoder] Success! Coords: {lat}, {lon}")
                
                # Cache results
                _cache[sanitized_address] = [lat, lon]
                save_cache(_cache)
                return lat, lon
            else:
                print(f"[Geocoder] No geocoding result found for: {sanitized_address}. Using fallback.")
        else:
            print(f"[Geocoder] Nominatim API returned status {res.status}. Using fallback.")
            
    except Exception as e:
        print(f"[Geocoder] Error contacting geocoding service: {e}. Using fallback.")
        
    # 3. Fallback
    fallback_coords = get_state_fallback(sanitized_address)
    # Save the fallback to cache to prevent hit on OSM in the future
    _cache[sanitized_address] = list(fallback_coords)
    save_cache(_cache)
    return fallback_coords
