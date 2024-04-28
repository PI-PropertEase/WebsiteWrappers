import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, Mock
from Wrappers.models import set_property_internal_id
from Wrappers.regular_events_handler import handle_recv
from Wrappers.zooking.zooking_wrapper import ZookingWrapper
from Wrappers.zooking.converters.zooking_to_propertease import ZookingToPropertease
from ProjectUtils.MessagingService.schemas import MessageFactory, to_json
from ProjectUtils.MessagingService.queue_definitions import (
    EXCHANGE_NAME,
    WRAPPER_TO_APP_ROUTING_KEY,
)
from pydantic import BaseModel
from requests import Response


# required for the fake_user fixture
class User(BaseModel):
    email: str


@pytest.fixture
def fake_user():
    return User(email="coolguy@gmail.com")


def test_import_properties_zooking_empty_db(mocker: MockerFixture, fake_user: User):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    wrapper = ZookingWrapper(queue="zooking_regular_queue")
    message_body = to_json(MessageFactory.create_import_properties_message(fake_user))

    user_properties_response = [
                {"user_email":"cool_guy@gmail.com","name":"Cool house 🦼🛹","address":"Morada Miguel","curr_price":50.0,"description":"descrição não interessa a ninguém","number_of_guests":4,"square_meters":250,"bedrooms":{"bedroom_1":[{"number_beds":2,"bed_type":"king_bed"},{"number_beds":1,"bed_type":"single_bed"}]},"bathrooms":[{"name":"bathroom_groundfloor","bathroom_fixtures":["toilet","tub"]}],"amenities":["AC","wifi"],"additional_info":"Se cá aparecerem, recebem um rebuçado","id":11},
                {"user_email":"cool_guy@gmail.com","name":"A mais fixe de todas 🪂🛸","address":"Morada João","curr_price":50.0,"description":"descrição não interessa a ninguém","number_of_guests":4,"square_meters":250,"bedrooms":{"bedroom_1":[{"number_beds":2,"bed_type":"king_bed"},{"number_beds":1,"bed_type":"single_bed"}]},"bathrooms":[{"name":"bathroom_groundfloor","bathroom_fixtures":["toilet","tub"]}],"amenities":["AC","wifi"],"additional_info":"Se cá aparecerem, recebem um rebuçado","id":12}
            ]

    mock_response = Mock()
    mock_response.json.return_value = user_properties_response
    # mock requests.get to return predefined JSON
    mocker.patch("requests.get", return_value=mock_response)

    mocker.patch("Wrappers.models.set_property_internal_id", return_value=1)

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    properties_after_conversion = [ZookingToPropertease.convert_property(prop) for prop in user_properties_response]

    expected_body = to_json(MessageFactory.create_import_properties_response_message(
        service=wrapper.service_schema, properties=[ZookingToPropertease.convert_property(prop) for prop in user_properties_response]
    ))

    # asserts
    # 1. assert basic_publish called with - o tipo de mensagem esperado + o body esperado
    channel_mock.basic_publish.assert_called_once_with(
        exchange=EXCHANGE_NAME,
        routing_key=WRAPPER_TO_APP_ROUTING_KEY,
        body=expected_body,
    )
    # 2. assert que a mensagem foi acknowledged (basic_ack called i guess?)
    channel_mock.basic_ack.assert_called_once()
    # 3. assert estado da DB quando acaba
    assert False == True
