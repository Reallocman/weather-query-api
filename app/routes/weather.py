import csv
import os
from datetime import datetime
from datetime import timedelta
from datetime import UTC
from io import StringIO

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import WeatherQuery
from app.services.weather_service import get_weather

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
RATE_LIMIT = os.getenv("RATE_LIMIT", "30/minute")

limiter = Limiter(key_func=get_remote_address)
@router.get("/weather/{city}")
@limiter.limit(RATE_LIMIT)
def weather(
    request: Request,
    city: str,
    unit: str = "metric",
    db: Session = Depends(get_db)
):
    if unit not in ["metric", "imperial"]:
        return {
            "error": "Invalid unit. Use 'metric' for Celsius or 'imperial' for Fahrenheit."
        }

    latest_query = (
        db.query(WeatherQuery)
        .filter(WeatherQuery.city == city)
        .filter(WeatherQuery.unit == unit)
        .order_by(WeatherQuery.created_at.desc())
        .first()
    )

    if latest_query:
        now = datetime.now(UTC)
        created_at = latest_query.created_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        time_difference = now - created_at

        if time_difference < timedelta(minutes=5):
            cached_query = WeatherQuery(
                city=city,
                temperature=latest_query.temperature,
                description=latest_query.description,
                unit=latest_query.unit,
                served_from_cache=True
            )

            db.add(cached_query)
            db.commit()

            return {
                "city": latest_query.city,
                "temperature": latest_query.temperature,
                "description": latest_query.description,
                "unit": latest_query.unit,
                "served_from_cache": True
            }  # noqa

    weather_data = get_weather(city, unit)

    if weather_data.get("cod") != 200:
        return weather_data

    new_query = WeatherQuery(
        city=city,
        temperature=weather_data["main"]["temp"],
        description=weather_data["weather"][0]["description"],
        unit=unit,
        served_from_cache=False
    )

    db.add(new_query)
    db.commit()

    return {
        "city": city,
        "temperature": weather_data["main"]["temp"],
        "description": weather_data["weather"][0]["description"],
        "unit": unit,
        "served_from_cache": False
    }  # noqa


@router.get("/history")
def history(
    limit: int = 10,
    offset: int = 0,
    city: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(WeatherQuery)

    if city:
        query = query.filter(
            WeatherQuery.city.ilike(f"%{city}%")
        )

    if date_from:
        parsed_date_from = datetime.fromisoformat(date_from)

        query = query.filter(
            WeatherQuery.created_at >= parsed_date_from
        )

    if date_to:
        parsed_date_to = (
            datetime.fromisoformat(date_to)
            + timedelta(days=1)
        )

        query = query.filter(
            WeatherQuery.created_at < parsed_date_to
        )

    total = query.count()

    queries = (
        query
        .order_by(WeatherQuery.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": queries
    }  # noqa


@router.get("/history/export")
def export_history(
    city: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(WeatherQuery)

    if city:
        query = query.filter(
            WeatherQuery.city.ilike(f"%{city}%")
        )

    if date_from:
        parsed_date_from = datetime.fromisoformat(date_from)

        query = query.filter(
            WeatherQuery.created_at >= parsed_date_from
        )

    if date_to:
        parsed_date_to = (
            datetime.fromisoformat(date_to)
            + timedelta(days=1)
        )

        query = query.filter(
            WeatherQuery.created_at < parsed_date_to
        )

    queries = (
        query
        .order_by(WeatherQuery.created_at.desc())
        .all()
    )

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "city",
        "temperature",
        "description",
        "unit",
        "served_from_cache",
        "created_at"
    ])

    for item in queries:
        writer.writerow([
            item.city,
            item.temperature,
            item.description,
            item.unit,
            item.served_from_cache,
            item.created_at
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=weather_history.csv"
        }
    )  # noqa