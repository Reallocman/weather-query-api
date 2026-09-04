from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

from fastapi import FastAPI
import json
import logging
import time

from fastapi import Request
from app.database import Base
from app.database import engine

from app.routes.weather import router as weather_router
from app.routes.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)

logger = logging.getLogger("weather_app")
app = FastAPI()

#Base.metadata.create_all(bind=engine)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()

    logger.info(
        json.dumps({
            "event": "request_start",
            "method": request.method,
            "path": request.url.path
        })
    )

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            json.dumps({
                "event": "request_error",
                "method": request.method,
                "path": request.url.path
            })
        )
        raise

    duration_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2
    )

    logger.info(
        json.dumps({
            "event": "request_end",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms
        })
    )

    return response
app.include_router(weather_router)
app.include_router(health_router)


@app.get("/")
def root():
    return {"message": "Weather API is running"}  # noqa