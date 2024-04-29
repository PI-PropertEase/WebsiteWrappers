import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, Mock, call
from Wrappers.regular_events_handler import handle_recv
from Wrappers.zooking.zooking_wrapper import ZookingWrapper
from ProjectUtils.MessagingService.schemas import MessageFactory, to_json
from tests.fixtures import fake_user, test_db
from Wrappers.models import ReservationStatus, set_property_internal_id, ReservationIdMapperZooking
from ProjectUtils.MessagingService.queue_definitions import (
    EXCHANGE_NAME,
    WRAPPER_TO_CALENDAR_ROUTING_KEY,
)
from ProjectUtils.MessagingService.schemas import Service
import Wrappers.zooking.converters.zooking_to_propertease
import Wrappers.regular_events_handler

"""
    Test for the message RESERVATION_IMPORT_INITIAL_REQUEST, when PropertyService
    doesn't detect any duplicate properties
"""
def test_reservation_import_handler_initial_request_zooking_no_duplicates(mocker: MockerFixture, fake_user):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    wrapper = ZookingWrapper(queue="zooking_regular_queue")
    message_body = to_json(MessageFactory.create_reservation_import_initial_request_message(
        email=fake_user.email,
        old_new_id_map=dict()
    ))

    user_reservations_response = [
        {"property_id":11,"client_email":"cool_client@gmail.com","client_name":"Test","client_phone":"+351911234567","arrival":"2024-05-01T12:00:00","departure":"2024-05-04T12:00:00","cost":150.0,"reservation_status":"confirmed","id":17},
        {"property_id":11,"client_email":"cool_client@gmail.com","client_name":"Test","client_phone":"+351911234567","arrival":"2024-05-04T16:00:00","departure":"2024-05-05T18:00:00","cost":150.0,"reservation_status":"pending","id":18}
    ]

    # set up property mapping
    property_11_internal_id = set_property_internal_id(Service.ZOOKING, 11)

    mock_requests_get = Mock()
    mock_response = Mock()
    mock_requests_get.return_value = mock_response
    mock_response.json.return_value = user_reservations_response
    mocker.patch("requests.get", mock_requests_get)
        
    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)

    create_reservations_spy = mocker.spy(Wrappers.zooking.converters.zooking_to_propertease, "create_reservation")

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    expected_body = to_json(MessageFactory.create_import_reservations_response_message(
        service=Service.ZOOKING,
        reservations=[
            {"_id": 1,"reservation_status": "confirmed","property_id": property_11_internal_id,"owner_email": "cool_guy@gmail.com","begin_datetime": "2024-05-01T12:00:00","end_datetime": "2024-05-04T12:00:00","client_email": "cool_client@gmail.com","client_name": "Test","client_phone": "+351911234567","cost": 150.0,},
            {"_id": 2,"reservation_status": "pending","property_id": property_11_internal_id,"owner_email": "cool_guy@gmail.com","begin_datetime": "2024-05-04T16:00:00","end_datetime": "2024-05-05T18:00:00","client_email": "cool_client@gmail.com","client_name": "Test","client_phone": "+351911234567","cost": 150.0,}
        ]
    ))

    # assert
    assert create_reservations_spy.call_count == 2
    expected_call_args = [
        call(Service.ZOOKING, 17, "confirmed"),
        call(Service.ZOOKING, 18, "pending"),
    ]
    assert create_reservations_spy.call_args_list == expected_call_args
    channel_mock.basic_publish.assert_called_once_with(
        exchange=EXCHANGE_NAME,
        routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY,
        body=expected_body,
    )
    channel_mock.basic_ack.assert_called_once()


"""
    Test for the message RESERVATION_IMPORT_INITIAL_REQUEST, but PropertyService
    detected two that this property is a duplicate
"""
def test_reservation_import_handler_initial_request_zooking_with_duplicates(mocker: MockerFixture, fake_user, test_db):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    wrapper = ZookingWrapper(queue="zooking_regular_queue")
    message_body = to_json(MessageFactory.create_reservation_import_initial_request_message(
        email=fake_user.email,
        old_new_id_map={"1": 4}
    ))

    user_reservations_response = [
        {"property_id":11,"client_email":"cool_client@gmail.com","client_name":"Test","client_phone":"+351911234567","arrival":"2024-05-01T12:00:00","departure":"2024-05-04T12:00:00","cost":150.0,"reservation_status":"confirmed","id":17},
        {"property_id":11,"client_email":"cool_client@gmail.com","client_name":"Test","client_phone":"+351911234567","arrival":"2024-05-04T16:00:00","departure":"2024-05-05T18:00:00","cost":150.0,"reservation_status":"pending","id":18}
    ]

    # set up property mapping. external: 11 <-> internal: 1 (at this point, but this test tests a message
    # that says 'the supplied property with internal id 1 is a duplicate, and the real internal id is 4')
    # so the property_11_internal_id should be 4
    property_11_internal_id = set_property_internal_id(Service.ZOOKING, 11) # gotta call the function
    property_11_internal_id = 4 # check comment

    mock_requests_get = Mock()
    mock_response = Mock()
    mock_requests_get.return_value = mock_response
    mock_response.json.return_value = user_reservations_response
    mocker.patch("requests.get", mock_requests_get)
        
    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)

    create_reservations_spy = mocker.spy(Wrappers.zooking.converters.zooking_to_propertease, "create_reservation")

    set_property_mapped_id_spy = mocker.spy(Wrappers.regular_events_handler, "set_property_mapped_id")

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    expected_body = to_json(MessageFactory.create_import_reservations_response_message(
        service=Service.ZOOKING,
        reservations=[
            {"_id": 1,"reservation_status": "confirmed","property_id": property_11_internal_id,"owner_email": "cool_guy@gmail.com","begin_datetime": "2024-05-01T12:00:00","end_datetime": "2024-05-04T12:00:00","client_email": "cool_client@gmail.com","client_name": "Test","client_phone": "+351911234567","cost": 150.0,},
            {"_id": 2,"reservation_status": "pending","property_id": property_11_internal_id,"owner_email": "cool_guy@gmail.com","begin_datetime": "2024-05-04T16:00:00","end_datetime": "2024-05-05T18:00:00","client_email": "cool_client@gmail.com","client_name": "Test","client_phone": "+351911234567","cost": 150.0,}
        ]
    ))

    # assert
    set_property_mapped_id_spy.assert_called_once_with(
        Service.ZOOKING,
        '1',
        4
    )
    assert create_reservations_spy.call_count == 2
    expected_call_args = [
        call(Service.ZOOKING, 17, "confirmed"),
        call(Service.ZOOKING, 18, "pending"),
    ]
    assert create_reservations_spy.call_args_list == expected_call_args
    channel_mock.basic_publish.assert_called_once_with(
        exchange=EXCHANGE_NAME,
        routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY,
        body=expected_body,
    )
    channel_mock.basic_ack.assert_called_once()

    