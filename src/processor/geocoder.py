# src/processor/geocoder.py
from geopy.geocoders import Nominatim
from functools import lru_cache
import logging
import json
import os

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Nominatim geocoder
geolocator = Nominatim(user_agent="cyber_news_visualizer")

CACHE_FILE = "data/geocache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

geocache = load_cache()

@lru_cache(maxsize=100)
def get_coordinates(location_name):
    """
    Geocode a location name into latitude and longitude.
    Uses a local cache to minimize external API calls.
    """
    if not location_name:
        return None, None

    # Clean the location name for easier matching
    clean_name = location_name.strip()
    clean_lower = clean_name.lower()

    # 1. Check local on-disk cache
    if clean_name in geocache:
        return geocache[clean_name]["lat"], geocache[clean_name]["lon"]

    # 2. Hardcoded fallback for common cyber-threat locations to dodge 429s
    FALLBACK_GEO_DICT = {
        'russia': (61.5240, 105.3188),
        'china': (35.8617, 104.1954),
        'iran': (32.4279, 53.6880),
        'north korea': (40.3399, 127.5101),
        'dprk': (40.3399, 127.5101),
        'united states': (37.0902, -95.7129),
        'us': (37.0902, -95.7129),
        'usa': (37.0902, -95.7129),
        'ukraine': (48.3794, 31.1656),
        'israel': (31.0461, 34.8516),
        'united kingdom': (55.3781, -3.4360),
        'uk': (55.3781, -3.4360),
        'germany': (51.1657, 10.4515),
        'france': (46.2276, 2.2137),
        'india': (20.5937, 78.9629),
        'washington, d.c.': (38.8951, -77.0364),
        'washington': (38.8951, -77.0364),
        'moscow': (55.7558, 37.6173),
        'beijing': (39.9042, 116.4074),
        'london': (51.5074, -0.1278),
    }

    if clean_lower in FALLBACK_GEO_DICT:
        lat, lon = FALLBACK_GEO_DICT[clean_lower]
        # Save to disk cache so we don't need to match it again
        geocache[clean_name] = {"lat": lat, "lon": lon}
        save_cache(geocache)
        return lat, lon

    try:
        location = geolocator.geocode(location_name, timeout=10)
        if location:
            coords = {"lat": location.latitude, "lon": location.longitude}
            geocache[location_name] = coords
            save_cache(geocache)
            logger.info(f"Geocoded: {location_name} -> {coords}")
            return coords["lat"], coords["lon"]
    except Exception as e:
        logger.error(f"Geocoding error for {location_name}: {e}")
    
    return None, None

if __name__ == "__main__":
    test_loc = "Washington, D.C."
    print(f"Coords: {get_coordinates(test_loc)}")
