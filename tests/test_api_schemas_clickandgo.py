"""
    Calls external APIs and validates the response schema against our expected schema.
"""

import pytest
import requests
from api_schemas.clickandgo_schema import CNGPropertyBase 
from api_schemas.base_schema import ReservationBase
from pydantic import ValidationError

CLICKANDGO_URL = "http://localhost:8002"

def test_clickandgo_property_schema():
    clickandgo_property = requests.get(f"{CLICKANDGO_URL}/properties/1")
    try:
        CNGPropertyBase.model_validate(clickandgo_property.json())
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail("Failed to validate Clickandgo API property schema.")


def test_clickandgo_reservation_schema():
    clickandgo_reservation = requests.get(f"{CLICKANDGO_URL}/reservations/9")
    try:
        ReservationBase.model_validate(clickandgo_reservation.json()[0])
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail("Failed to validate Clickandgo API reservation schema.")