from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class VehicleType(str, Enum):
    TATA_ACE_EV = "tata_ace_ev"
    ASHOK_LEYLAND_BADA_DOST = "ashok_leyland_bada_dost"
    MAHINDRA_BOLERO_PIK_UP = "mahindra_bolero_pik_up"
    EICHER_PRO_2059 = "eicher_pro_2059"
    VOLVO_FMX = "volvo_fmx"


class TimeOfDay(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class WeatherCondition(str, Enum):
    CLEAR = "clear"
    RAINY = "rainy"
    FOGGY = "foggy"
    HOT = "hot"
    HAZY = "hazy"


class EtaPredictionRequest(BaseModel):
    distance_km: float = Field(gt=0, description="Route distance in kilometres")
    vehicle_type: VehicleType
    time_of_day: TimeOfDay
    day_of_week: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    historical_avg_delay_for_route: float = Field(ge=0, description="Average delay in minutes for the route")
    weather_condition: WeatherCondition


class EtaPredictionResponse(BaseModel):
    predicted_eta_minutes: float
    model_version: str
    inference_ms: float

    model_config = ConfigDict(from_attributes=True)