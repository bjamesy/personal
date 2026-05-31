import time

import httpx

from app.config import settings

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
CACHE_TTL = 86400  # 24 hours

_cache: dict[tuple[str, str], tuple[list[dict], float]] = {}

INTENT_TYPES: dict[str, list[str]] = {
    "before_movie": ["restaurant"],
    "after_movie": ["restaurant", "bar"],
    "browsing": ["restaurant", "bar"],
}


async def fetch_nearby_restaurants(
    theatre_id: str,
    latitude: float,
    longitude: float,
    intent: str,
) -> list[dict]:
    cache_key = (theatre_id, intent)
    now = time.monotonic()

    if cache_key in _cache:
        results, expires_at = _cache[cache_key]
        if now < expires_at:
            return results

    async with httpx.AsyncClient() as client:
        response = await client.post(
            PLACES_URL,
            json={
                "textQuery": "dive bar cheap pub local tavern",
                "maxResultCount": 5,
                "rankPreference": "DISTANCE",
                "locationBias": {
                    "circle": {
                        "center": {"latitude": latitude, "longitude": longitude},
                        "radius": 200,
                    }
                },
            },
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": settings.google_places_api_key,
                "X-Goog-FieldMask": "places.displayName,places.rating,places.formattedAddress,places.googleMapsUri,places.id",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

    results = [
        {
            "name": p["displayName"]["text"],
            "rating": p.get("rating"),
            "address": p.get("formattedAddress"),
            "google_maps_url": p.get("googleMapsUri"),
            "place_id": p.get("id"),
            "place_metadata": p,
        }
        for p in data.get("places", [])
        if "displayName" in p
    ]

    _cache[cache_key] = (results, now + CACHE_TTL)
    return results
