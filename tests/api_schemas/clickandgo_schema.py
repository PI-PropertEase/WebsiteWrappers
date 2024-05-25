from enum import Enum
from typing import Optional

from .base_schema import ClosedTimeFrame, PropertyBase
from pydantic import BaseModel, ConfigDict


class CNGAmenity(str, Enum):
    WIFI_FREE = "wifi_free"
    PARKING = "parking"
    AC = "AC"
    PATIO = "patio"


class CNGBedType(str, Enum):
    QUEEN = "queen"
    KING = "king"
    SINGLE = "single"
    TWIN = "twin"


class CNGBedroom(BaseModel):
    number_beds: int
    bed_type: CNGBedType


class CNGBathroomFixtures(str, Enum):
    TUB = "tub"
    SHOWER = "shower"
    TOILET = "toilet"


class CNGBathroom(BaseModel):
    bathroom_fixtures: list[CNGBathroomFixtures]


class CNGUser(BaseModel):
    name: str
    phone_number: str
    languages: list[str]


class CNGHouseRules(BaseModel):
    check_in: str  # string in format "00:00-10:00" (2 hours separated by hifen)
    check_out: str
    smoking_allowed: bool
    parties_allowed: bool
    rest_time: str
    pets_allowed: bool


class CNGPropertyBase(PropertyBase):
    model_config = ConfigDict(extra="forbid")
    description: str
    town: str
    guest_num: int
    house_area: int
    bedrooms: dict[str, list[CNGBedroom]]
    bathrooms: list[CNGBathroom]
    available_amenities: list[CNGAmenity]
    house_rules: CNGHouseRules
    additional_info: str
    cancellation_policy: str
    house_managers: list[CNGUser]
    closed_time_frames: dict[int, ClosedTimeFrame]