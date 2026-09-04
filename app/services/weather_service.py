import os
from pathlib import Path

import requests
from dotenv import load_dotenv

import json
import logging
import time
logger = logging.getLogger("weather_app")
BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather(city: str, unit: str = "metric"):

    if not API_KEY:
        return {
            "cod": 500,
            "message": "OPENWEATHER_API_KEY is missing"
        }

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": unit
    }
    start_time = time.perf_counter()
    response = requests.get(
        url,
        params=params,
        timeout=5
    )
    latency_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2
    )

    logger.info(
        json.dumps({
            "event": "external_api_call",
            "service": "openweather",
            "city": city,
            "unit": unit,
            "status_code": response.status_code,
            "latency_ms": latency_ms
        })
    )
    response.raise_for_status()

    return response.json()  # noqa
