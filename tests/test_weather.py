from unittest.mock import Mock

import pytest
from fastapi import HTTPException

import app.routes.weather as weather_module
import app.services.weather_service as weather_service_module
from app.models import WeatherQuery


def test_weather_uses_cache(client, monkeypatch):
    mock_get_weather = Mock(
        return_value={
            "cod": 200,
            "main": {
                "temp": 20.5
            },
            "weather": [
                {
                    "description": "clear sky"
                }
            ]
        }
    )

    monkeypatch.setattr(
        weather_module,
        "get_weather",
        mock_get_weather
    )

    first_response = client.get(
        "/weather/Rome?unit=metric"
    )

    assert first_response.status_code == 200
    assert first_response.json()["served_from_cache"] is False

    second_response = client.get(
        "/weather/Rome?unit=metric"
    )

    assert second_response.status_code == 200
    assert second_response.json()["served_from_cache"] is True

    assert mock_get_weather.call_count == 1  # noqa

def test_rate_limit_returns_429_and_does_not_write_to_db(
    client,
    db_session,
    monkeypatch
):
    mock_get_weather = Mock(
        return_value={
            "cod": 200,
            "main": {
                "temp": 20.5
            },
            "weather": [
                {
                    "description": "clear sky"
                }
            ]
        }
    )

    monkeypatch.setattr(
        weather_module,
        "get_weather",
        mock_get_weather
    )

    weather_module.limiter.reset()

    for _ in range(30):
        response = client.get(
            "/weather/London?unit=metric"
        )
        assert response.status_code == 200

    rows_before = (
        db_session.query(WeatherQuery)
        .filter(WeatherQuery.city == "London")
        .count()
    )

    blocked_response = client.get(
        "/weather/London?unit=metric"
    )

    assert blocked_response.status_code == 429

    rows_after = (
        db_session.query(WeatherQuery)
        .filter(WeatherQuery.city == "London")
        .count()
    )

    assert rows_after == rows_before  # noqa

def test_history_filtering_and_pagination(client, db_session):
    records = [
        WeatherQuery(
            city="Rome",
            temperature=20,
            description="clear",
            unit="metric",
            served_from_cache=False,
        ),
        WeatherQuery(
            city="Rome",
            temperature=21,
            description="cloudy",
            unit="metric",
            served_from_cache=False,
        ),
        WeatherQuery(
            city="London",
            temperature=15,
            description="rain",
            unit="metric",
            served_from_cache=False,
        ),
    ]

    db_session.add_all(records)
    db_session.commit()

    response = client.get(
        "/history?city=rom&limit=1&offset=0"
    )

    assert response.status_code == 200

    data = response.json()

    # Case-insensitive substring filtering
    assert data["total"] == 2
    assert len(data["items"]) == 1
    assert data["items"][0]["city"] == "Rome"

    # Second page
    response = client.get(
        "/history?city=rom&limit=1&offset=1"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 1
    assert data["items"][0]["city"] == "Rome"  # noqa

def test_weather_unknown_city_returns_404(client, monkeypatch):
    mock_get_weather = Mock(
        side_effect=HTTPException(status_code=404, detail="City not found")
    )

    monkeypatch.setattr(
        weather_module,
        "get_weather",
        mock_get_weather
    )

    response = client.get("/weather/Nowhereville?unit=metric")

    assert response.status_code == 404
    assert response.json()["detail"] == "City not found"

def test_get_weather_openweather_404_raises_http_exception(monkeypatch):
    mock_response = Mock(status_code=404)

    monkeypatch.setattr(
        weather_service_module.requests,
        "get",
        Mock(return_value=mock_response)
    )

    with pytest.raises(HTTPException) as exc_info:
        weather_service_module.get_weather("Nowhereville")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "City not found"

def test_weather_invalid_unit_returns_400(client):
    response = client.get("/weather/Rome?unit=bogus")

    assert response.status_code == 400
    assert "Invalid unit" in response.json()["detail"]

def test_history_malformed_date_returns_422(client):
    response = client.get("/history?date_from=not-a-date")

    assert response.status_code == 422

def test_history_export_returns_csv(client, db_session):
    db_session.add(
        WeatherQuery(
            city="Rome",
            temperature=20,
            description="clear",
            unit="metric",
            served_from_cache=False,
        )
    )
    db_session.commit()

    response = client.get("/history/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

    body = response.text
    assert "city,temperature,description,unit,served_from_cache,created_at" in body
    assert "Rome" in body  # noqa