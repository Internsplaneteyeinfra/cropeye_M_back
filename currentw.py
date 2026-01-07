from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
import httpx, uvicorn
from cachetools import TTLCache

# FastAPI App
app = FastAPI(title="WeatherAPI with Lat/Lon")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Rate Limiter (10 requests per minute per IP)
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# In-memory cache: max 500 entries, each cached for 1800 seconds (30 mins)
cache = TTLCache(maxsize=4000, ttl=1800)

API_KEY = "a7977cf38bb044e9a4d82500252008"   # generated using dev1 gmail account
BASE_URL = "https://api.weatherapi.com/v1/current.json"

@app.get("/current-weather")
# @limiter.limit("100/minute")  # limit per IP
async def get_curr_weather(
    request: Request,
    lat: float = Query(None, description="Latitude"),
    lon: float = Query(None, description="Longitude"),
    city: str = Query(None, description="City name (optional if lat/lon given)")
):
    # Build query string
    if lat is not None and lon is not None:
        q = f"{lat},{lon}"
    elif city:
        q = city
    else:
        raise HTTPException(400, "Provide either city or lat/lon")

    # Check cache first
    if q in cache: 
        return cache[q]

    # Prepare request to WeatherAPI
    params = {"key": API_KEY, "q": q, "aqi": "yes"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(BASE_URL, params=params)
        if r.status_code != 200:
            raise HTTPException(502, f"WeatherAPI error: {r.text}")
        data = r.json()

    # Handle WeatherAPI errors (like quota exceeded)
    if "error" in data:
        err = data["error"]
        code = err.get("code")
        message = err.get("message", "Unknown WeatherAPI error")
        raise HTTPException(429 if code == 2007 else 502, detail=message)

    current = data["current"]
    response = {
        "location": data["location"]["name"],
        "region": data["location"]["region"],
        "country": data["location"]["country"],
        "localtime": data["location"]["localtime"],
        "latitude": data["location"]["lat"],
        "longitude": data["location"]["lon"],

        # Weather details
        "temperature_c": current["temp_c"], 
        "humidity": current["humidity"],
        "wind_kph": current["wind_kph"],
        "precip_mm": current["precip_mm"],   
    }

    # Save to cache
    cache[q] = response
    return response

if __name__ == "__main__":
    uvicorn.run("currentw:app", host="0.0.0.0", port=9005, reload=False)
