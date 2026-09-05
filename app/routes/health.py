import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.database import SessionLocal

router = APIRouter()
logger = logging.getLogger("weather_app")

@router.get("/health")
def health():
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected"
        }  # noqa

    except Exception:
        logger.exception("Health check failed: database connectivity error")

        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "disconnected"
            }
        )

    finally:
        db.close()
