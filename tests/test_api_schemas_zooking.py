"""
    Calls external APIs and validates the response schema against our expected schema.
"""

import pytest
import requests
from api_schemas.zooking_schema import ZookingPropertyBase
from api_schemas.base_schema import ReservationBase
from pydantic import ValidationError

ZOOKING_URL = "http://localhost:8000"

def test_zooking_property_schema():
    zooking_property = requests.get(f"{ZOOKING_URL}/properties/1")
    try:
        ZookingPropertyBase.model_validate(zooking_property.json())
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail("Failed to validate Zooking API property schema.")


def test_zooking_reservation_schema():
    # this endpoint returns an array of reservations for property 10
    zooking_reservation = requests.get(f"{ZOOKING_URL}/reservations/9")
    try:
        ReservationBase.model_validate(zooking_reservation.json()[0])
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail("Failed to validate Zooking API reservation schema.")