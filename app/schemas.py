from datetime import datetime

from pydantic import BaseModel


class WeatherHistoryResponse(BaseModel):
    id: int
    city: str
    temperature: float
    description: str
    unit: str
    served_from_cache: bool
    created_at: datetime

    class Config:
        from_attributes = True  # noqa