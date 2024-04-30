import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, Mock, call
from ProjectUtils.MessagingService.schemas import MessageFactory, to_json
from tests.fixtures import fake_user, test_db
from Wrappers.models import ReservationStatus, create_reservation
from ProjectUtils.MessagingService.schemas import Service
from Wrappers.zooking.zooking_wrapper import ZookingWrapper
import Wrappers.zooking.zooking_wrapper
from Wrappers.scheduled_events_handler import handle_recv

"""
    Test for the message RESERVATION_IMPORT_OVERLAP, received when an imported
    reservation sent to CalendarService is detected as overlapping another existing
    reservation/event for the same property.
"""
# TODO: this message might not delete the overlapping property, it might
# just update its status to "cancelled". If we change it to update,
# we need to assert that update_reservation was called for this reservation,
# and same thing for the PUT request     
def test_reservation_import_overlap_zooking(mocker: MockerFixture, fake_user, test_db):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    external_reservation_id = 17

    # create reservation on wrappers DB
    reservation_in_db = create_reservation(
        service=Service.ZOOKING,
        external_reservation_id=external_reservation_id,
        reservation_status="confirmed"
    )
    
    test_reservation = {
            "_id": reservation_in_db.internal_id,
            "reservation_status": "pending",
            "property_id": "1",
            "owner_email": "cool_guy@gmail.com",
            "begin_datetime": "2024-05-01T12:00:00",
            "end_datetime": "2024-05-04T12:00:00",
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351911234567",
            "cost": 150.0,
        }
    wrapper = ZookingWrapper(queue="zooking_regular_queue")
    message_body = to_json(MessageFactory.create_overlap_import_reservation_message(
        ex_reservation=test_reservation,
    ))

    mock_requests_delete = Mock()
    mocker.patch("requests.delete", mock_requests_delete)

    get_reservation_external_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_reservation_external_id")
        
    #update_reservation_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "update_reservation")

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    # assert
    get_reservation_external_id_spy.assert_called_once_with(
        Service.ZOOKING, reservation_in_db.internal_id
    )
    mock_requests_delete.assert_called_once_with(
        url=wrapper.url + f"reservations/{external_reservation_id}"
    )
    channel_mock.basic_ack.assert_called_once()
    #update_reservation_spy.assert_called_once_with(
    #    Service.ZOOKING, reservation_in_db.internal_db, ReservationStatus.CANCELED
    #)

