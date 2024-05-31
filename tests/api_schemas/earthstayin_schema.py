from enum import Enum
from typing import Optional

from .base_schema import PropertyBase
from pydantic import BaseModel, ConfigDict


class EarthStayinAmenity(str, Enum):
    WIFI = "free_wifi"
    OPEN_PARKING = "car_parking"
    AC = "AC"


class EarthStayinBedType(str, Enum):
    QUEEN_BED = "queen_bed"
    KING_BED = "king_bed"
    SINGLE_BED = "single_bed"
    TWIN_BED = "twin_bed"


class EarthStayinBedroom(BaseModel):
    number_beds: int
    bed_type: EarthStayinBedType


class EarthStayinBathroomFixtures(str, Enum):
    TUB = "tub"
    SHOWER = "shower"
    TOILET = "toilet"
    BIDET = "bidet"


class EarthStayinBathroom(BaseModel):
    name: str
    bathroom_fixtures: list[EarthStayinBathroomFixtures]


class EarthStayinHouseRules(BaseModel):
    checkin_time: str
    checkout_time: str
    smoking_allowed: bool
    rest_time: str
    pets_allowed: bool


class EarthStayinPropertyBase(PropertyBase):
    model_config = ConfigDict(extra="forbid")
    description: str
    city: str
    number_of_guests: int
    square_meters: int
    bedrooms: dict[str, list[EarthStayinBedroom]]
    bathrooms: list[EarthStayinBathroom]
    amenities: list[EarthStayinAmenity]
    accessibilities: list[str]
    additional_info: str
    house_rules: EarthStayinHouseRules
