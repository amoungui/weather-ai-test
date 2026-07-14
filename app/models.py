from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class WeatherRequest(BaseModel):
    lat: float = Field(..., description="Latitude of the location", example=-1.2921)
    lon: float = Field(..., description="Longitude of the location", example=36.8219)
    days: Optional[int] = Field(7, ge=1, le=16, description="Number of days for the forecast", example=3)   
    ai: Optional[bool] = Field(True, description="Whether to use AI for the forecast", example=True)  
    units: Optional[str] = Field("metric", pattern="^(metric|imperial)$", description="Units for the forecast (metric or imperial)", example="metric") 
    lang: Optional[str] = Field("en", description="Language for the forecast", example="en")    

class WeatherResponse(BaseModel):
    current: Dict[str, Any] = Field(..., description="Current weather data including temperature, humidity, wind speed, and other relevant information")
    forecast: List[Dict[str, Any]] = Field(..., description="List of daily forecasts with date, temperature, weather condition, and other relevant data")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary of the weather forecast")  
    location: Dict[str, Any] = Field(..., description="Location information including name, region, country, and coordinates")
    timestamp: datetime = Field(..., description="Timestamp of the weather data retrieval in ISO 8601 format")  

class UsageResponse(BaseModel):
    requests_used: int
    requests_limit: int
    ai_requests_used: int
    ai_requests_limit: int
    period_start: datetime
    period_end: datetime
    plan: str
    remaining: int


