"""
    Calls external APIs and validates the response schema against our expected schema.
"""

import pytest
import requests
from api_schemas.earthstayin_schema import EarthStayinPropertyBase
from api_schemas.base_schema import ReservationBase
from pydantic import ValidationError

EARTHSTAYIN_URL = "http://localhost:8001"

def test_earthstayin_property_schema():
    earthstayin_property = requests.get(f"{EARTHSTAYIN_URL}/properties/1")
    try:
        EarthStayinPropertyBase.model_validate(earthstayin_property.json())
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail("Failed to validate Earthstayin API property schema.")


def test_earthstayin_reservation_schema():
    # this endpoint returns an array of reservations for property 10
    earthstayin_reservation = requests.get(f"{EARTHSTAYIN_URL}/reservations/9")
    try:
        ReservationBase.model_validate(earthstayin_reservation.json()[0])
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail("Failed to validate Earthstayin API reservation schema.")