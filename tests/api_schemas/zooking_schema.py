from enum import Enum
from typing import Optional

from .base_schema import PropertyBase
from pydantic import BaseModel


class ZookingAmenity(str, Enum):
    WIFI = "wifi"
    OPEN_PARKING = "open_parking"
    AC = "AC"


class ZookingBedType(str, Enum):
    QUEEN_BED = "queen_bed"
    KING_BED = "king_bed"
    SINGLE_BED = "single_bed"


class ZookingBedroom(BaseModel):
    number_beds: int
    bed_type: ZookingBedType


class ZookingBathroomFixtures(str, Enum):
    TUB = "tub"
    SHOWER = "shower"
    TOILET = "toilet"


class ZookingBathroom(BaseModel):
    name: str
    bathroom_fixtures: list[ZookingBathroomFixtures]


class ZookingPropertyBase(PropertyBase):
    description: str
    number_of_guests: int
    square_meters: int
    bedrooms: dict[str, list[ZookingBedroom]]
    bathrooms: list[ZookingBathroom]
    amenities: list[ZookingAmenity]
    additional_info: str