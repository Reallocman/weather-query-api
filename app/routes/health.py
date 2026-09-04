from fastapi import APIRouter

from sqlalchemy import text

from app.database import SessionLocal

router = APIRouter()


@router.get("/health")
def health():
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected"
        }  # noqa


    except Exception as e:

        return {

            "status": "error",

            "database": "disconnected",

            "details": str(e)

        }

    finally:
        db.close()