"""
    Calls external APIs and validates the response schema against our expected schema.
"""

import pytest
import requests
from api_schemas.zooking_schema import ZookingPropertyBase
from api_schemas.clickandgo_schema import CNGPropertyBase 
from api_schemas.earthstayin_schema import EarthStayinPropertyBase
from api_schemas.base_schema import ReservationBase # all APIs use this schema for reservations
from pydantic import ValidationError
import traceback

ZOOKING_URL = "http://localhost:8000"
EARTHSTAYIN_URL = "http://localhost:8001"
CLICKANDGO_URL = "http://localhost:8002"

def test_zooking_property_schema():
    zooking_property = requests.get(f"{ZOOKING_URL}/properties/1")
    print("zooking propertyy!!!", zooking_property.json())
    try:
        ZookingPropertyBase.model_validate(zooking_property.json())
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail(f"Failed to validate Zooking API property schema. Error:\n {traceback.print_exc()}")


def test_zooking_reservation_schema():
    # this endpoint returns an array of reservations for property 10
    zooking_reservation = requests.get(f"{ZOOKING_URL}/reservations/9")
    try:
        ReservationBase.model_validate(zooking_reservation.json()[0])
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail(f"Failed to validate Zooking API reservation schema. Error:\n {traceback.print_exc()}")


def test_earthstayin_property_schema():
    earthstayin_property = requests.get(f"{EARTHSTAYIN_URL}/properties/1")
    try:
        EarthStayinPropertyBase.model_validate(earthstayin_property.json())
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail(f"Failed to validate Earthstayin API property schema. Error:\n {traceback.print_exc()}")


def test_earthstayin_reservation_schema():
    # this endpoint returns an array of reservations for property 10
    earthstayin_reservation = requests.get(f"{EARTHSTAYIN_URL}/reservations/9")
    try:
        ReservationBase.model_validate(earthstayin_reservation.json()[0])
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail(f"Failed to validate Earthstayin API reservation schema. Error:\n {traceback.print_exc()}")


def test_clickandgo_property_schema():
    clickandgo_property = requests.get(f"{CLICKANDGO_URL}/properties/1")
    try:
        CNGPropertyBase.model_validate(clickandgo_property.json())
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail(f"Failed to validate Clickandgo API property schema. Error:\n {traceback.print_exc()}")


def test_clickandgo_reservation_schema():
    # this endpoint returns an array of reservations for property 10
    clickandgo_reservation = requests.get(f"{CLICKANDGO_URL}/reservations/9")
    try:
        ReservationBase.model_validate(clickandgo_reservation.json()[0])
    except (ValidationError, requests.exceptions.JSONDecodeError):
        pytest.fail(f"Failed to validate Clickandgo API reservation schema. Error:\n {traceback.print_exc()}")