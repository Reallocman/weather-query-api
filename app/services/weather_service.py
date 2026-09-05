import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

import json
import logging
import time
logger = logging.getLogger("weather_app")
BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather(city: str, unit: str = "metric"):

    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENWEATHER_API_KEY is missing"
        )

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": unit
    }
    start_time = time.perf_counter()

    try:
        response = requests.get(
            url,
            params=params,
            timeout=5
        )
    except requests.exceptions.RequestException as exc:
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
                "status_code": None,
                "latency_ms": latency_ms
            })
        )

        raise HTTPException(
            status_code=502,
            detail="Unable to reach the weather service"
        ) from exc

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

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="City not found")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Weather service returned an error"
        )

    return response.json()  # noqa
