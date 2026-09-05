# Weather Query API

A FastAPI-based weather service that fetches current weather data from OpenWeatherMap, stores query history in PostgreSQL, and provides caching, filtering, pagination, CSV export, rate limiting, database migrations, structured logging, automated tests, and Docker deployment.

## Features

* Current weather lookup by city
* Celsius and Fahrenheit support
* PostgreSQL query history
* 5-minute database-backed cache
* Cached requests are still recorded in history
* Case-insensitive city filtering
* Date range filtering
* Pagination
* CSV export
* Per-IP rate limiting
* Health check endpoint
* Alembic database migrations
* Structured logging
* Docker Compose deployment
* Automated tests with pytest

## Tech Stack

* Python 3.13
* FastAPI
* SQLAlchemy
* PostgreSQL
* Alembic
* OpenWeatherMap API
* SlowAPI
* Docker / Docker Compose
* pytest

## Project Structure

```
weather-app/
├── alembic/
│   └── versions/
├── app/
│   ├── routes/
│   │   ├── health.py
│   │   └── weather.py
│   ├── services/
│   │   └── weather_service.py
│   ├── database.py
│   ├── main.py
│   └── models.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_weather.py
├── .env.sample
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Environment Variables

Create a `.env` file in the project root.

Example:

```
OPENWEATHER_API_KEY=your_openweather_api_key
DATABASE_URL=postgresql://weather_user:weather_password@localhost:5432/weather_db
RATE_LIMIT=30/minute
```

Do not commit `.env` to Git.

When running the complete application through Docker Compose, the application container uses the PostgreSQL service hostname `db`.

## Run with Docker Compose

The recommended way to run the project is Docker Compose:

```
docker compose up --build
```

Docker Compose starts:

* PostgreSQL
* FastAPI application
* Alembic migrations before application startup

The API will be available at:

```
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```
http://127.0.0.1:8000/docs
```

Stop the containers:

```
docker compose down
```

## Local Development

Start only PostgreSQL:

```
docker compose up -d db
```

Install dependencies:

```
pip install -r requirements.txt
```

Apply database migrations:

```
alembic upgrade head
```

Start FastAPI:

```
uvicorn app.main:app --reload
```

## API Endpoints

### Get Current Weather

```
GET /weather/{city}
```

Example:

```
GET /weather/Rome?unit=metric
```

Supported units:

* `metric` — Celsius
* `imperial` — Fahrenheit

Example response:

```
{
  "city": "Rome",
  "temperature": 25.4,
  "description": "clear sky",
  "unit": "metric",
  "served_from_cache": false
}
```

If the same city and unit combination was queried within the last 5 minutes, the previous weather data is reused and `served_from_cache` is `true`.

A new history record is still created for the cached request.

## History

```
GET /history
```

Default pagination:

```
limit=10
offset=0
```

Example:

```
/history?limit=10&offset=0
```

### Filter by City

City filtering is case-insensitive and supports substring matching:

```
/history?city=rom
```

### Filter by Date Range

```
/history?date_from=2026-09-01&date_to=2026-09-04
```

Filters and pagination can be combined:

```
/history?city=rom&date_from=2026-09-01&date_to=2026-09-04&limit=10&offset=0
```

## CSV Export

```
GET /history/export
```

History filters are also supported:

```
/history/export?city=Rome
```

The endpoint returns weather query history as a CSV file.

## Health Check

```
GET /health
```

Example successful response:

```
{
  "status": "ok",
  "database": "connected"
}
```

## Cache

The application checks the latest stored query for the same city and unit.

If the query is less than 5 minutes old:

* OpenWeatherMap is not called again
* Stored weather data is reused
* A new history record is created
* `served_from_cache` is set to `true`

The cache is backed by PostgreSQL, so it survives application restarts.

## Rate Limiting

Weather requests are rate-limited per IP address.

The default configuration is:

```
RATE_LIMIT=30/minute
```

When the limit is exceeded, the API returns:

```
HTTP 429 Too Many Requests
```

Rejected requests do not create database records.

## Database Migrations

Database schema changes are managed with Alembic.

Apply migrations:

```
alembic upgrade head
```

Check the current migration:

```
alembic current
```

Create a migration after changing SQLAlchemy models:

```
alembic revision --autogenerate -m "description"
```

## Tests

Run the test suite:

```
pytest -v
```

The tests cover:

* Fresh weather request and cache reuse
* Mocked external weather API
* Rate limiting and HTTP 429
* Verification that rejected requests do not write to the database
* Case-insensitive history filtering
* Pagination

Current expected result:

```
3 passed
```

Tests use a separate in-memory SQLite database and do not modify the PostgreSQL development database.

## Structured Logging

The application logs:

* Request start
* Request end
* HTTP method
* Request path
* Response status code
* Request duration
* Errors
* External OpenWeatherMap API latency

Example:

```
{"event": "request_start", "method": "GET", "path": "/weather/Rome"}

{"event": "external_api_call", "service": "openweather", "city": "Rome", "unit": "metric", "status_code": 200, "latency_ms": 153.4}

{"event": "request_end", "method": "GET", "path": "/weather/Rome", "status_code": 200, "duration_ms": 165.2}
```

Cached requests do not generate an `external_api_call` event.

## Security

The OpenWeatherMap API key and other configuration values are loaded from environment variables.

Never commit the `.env` file or real API keys to the repository.

Use `.env.sample` as the configuration template.

## Original assignment

The original technical assignment is available in [`docs/test-assignment.docx`](docs/test-assignment.docx).