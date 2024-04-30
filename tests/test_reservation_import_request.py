import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, Mock, call
from ProjectUtils.MessagingService.schemas import MessageFactory, to_json
from tests.fixtures import fake_user, test_db
from Wrappers.models import ReservationStatus, create_reservation, set_property_internal_id
from ProjectUtils.MessagingService.schemas import Service
from Wrappers.zooking.zooking_wrapper import ZookingWrapper
import Wrappers.zooking.zooking_wrapper
import Wrappers.zooking.converters.zooking_to_propertease
from Wrappers.scheduled_events_handler import handle_recv
from ProjectUtils.MessagingService.queue_definitions import EXCHANGE_NAME, WRAPPER_TO_CALENDAR_ROUTING_KEY

"""
    Test the RESERVATION_IMPORT_REQUEST message. Its a periodic message
    that requests the wrapper to import new reservations, or reservations
    whose state changed from confirmed/pending to cancelled
"""




# Tests:

#   6. Testar receber uma reserva de uma propriedade que nao existe no nosso sistema yet

"""
    Test fetching reservations and detecting new reservations.
"""
def test_reservation_import_zooking_new_reservations(mocker: MockerFixture, fake_user, test_db):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    external_reservation_id = 17
    external_property_id = 1

    # populate wrappers DB with a single reservation
    create_reservation(
        service=Service.ZOOKING,
        external_reservation_id=external_reservation_id,
        reservation_status="confirmed"
    )

    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)


    # external property 1 should be mapped in our DB aswell
    internal_property_id = set_property_internal_id(Service.ZOOKING, external_property_id)
    
    # 2 new reservations, since 17 is already saved on wrappers_db
    user_reservations_response = [
        {
            "id": 17,
            "property_id": external_property_id,
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351911234567",
            "begin_datetime": "2024-05-01T12:00:00",
            "end_datetime": "2024-05-04T12:00:00",
            "cost": 150.0,
            "reservation_status": "pending",
        },
        {
            "id": 18,
            "property_id": external_property_id,
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351911234567",
            "begin_datetime": "2024-05-05T12:00:00",
            "end_datetime": "2024-05-06T12:00:00",
            "cost": 150.0,
            "reservation_status": "confirmed",
        },
        {
            "id": 19,
            "property_id": external_property_id,
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351911234567",
            "begin_datetime": "2024-05-08T12:00:00",
            "end_datetime": "2024-05-12T12:00:00",
            "cost": 150.0,
            "reservation_status": "confirmed",
        },
    ]


    wrapper = ZookingWrapper(queue="zooking_regular_queue")
    
    fake_user.connected_services = [wrapper.service_schema]
    message_body = to_json(MessageFactory.create_import_reservations_message(
        users=[fake_user],
    ))

    mock_requests_get = Mock()
    mock_response = Mock()
    mock_requests_get.return_value = mock_response
    mock_response.json.return_value = user_reservations_response
    mocker.patch("requests.get", mock_requests_get)

    get_reservation_external_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_reservation_by_external_id")
        
    get_property_internal_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_property_internal_id")

    create_reservations_spy = mocker.spy(Wrappers.zooking.converters.zooking_to_propertease, "create_reservation")

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    expected_body = to_json(MessageFactory.create_import_reservations_response_message(wrapper.service_schema,
        [
            {
                "_id": 2,
                "reservation_status": user_reservations_response[1].get("reservation_status"),
                "property_id": internal_property_id,
                "owner_email": fake_user.email,
                "begin_datetime":  user_reservations_response[1].get("arrival"),
                "end_datetime":  user_reservations_response[1].get("departure"),
                "client_email": user_reservations_response[1].get("client_email"),
                "client_name": user_reservations_response[1].get("client_name"),
                "client_phone": user_reservations_response[1].get("client_phone"),
                "cost": user_reservations_response[1].get("cost"),
            },
            {
                "_id": 3,
                "reservation_status": user_reservations_response[2].get("reservation_status"),
                "property_id": internal_property_id,
                "owner_email": fake_user.email,
                "begin_datetime":  user_reservations_response[2].get("arrival"),
                "end_datetime":  user_reservations_response[2].get("departure"),
                "client_email": user_reservations_response[2].get("client_email"),
                "client_name": user_reservations_response[2].get("client_name"),
                "client_phone": user_reservations_response[2].get("client_phone"),
                "cost": user_reservations_response[2].get("cost"),
            }
        ]
    ))

    # assert
    assert get_property_internal_id_spy.call_count == 3
    call_args_property_internal = [
        call(wrapper.service_schema, external_property_id),
        call(wrapper.service_schema, external_property_id),
        call(wrapper.service_schema, external_property_id),
    ]
    assert get_property_internal_id_spy.call_args_list == call_args_property_internal
    assert get_reservation_external_id_spy.call_count == 3
    call_args_reservation_external = [
        call(wrapper.service_schema, 17),
        call(wrapper.service_schema, 18),
        call(wrapper.service_schema, 19),
    ]
    assert get_reservation_external_id_spy.call_args_list == call_args_reservation_external
    create_reservations_spy.call_count == 2 # 2 new reservations
    mock_requests_get.assert_called_once_with(
        url=wrapper.url + f"reservations/upcoming?email={fake_user.email}"
    )
    channel_mock.basic_publish.assert_called_once_with(
        exchange=EXCHANGE_NAME,
        routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY,
        body=expected_body,
    )
    channel_mock.basic_ack.assert_called_once()


"""
    Test fetching reservations and there are no new reservations/reservations that changed
    their status. No message should be published to CalendarService
"""
def test_reservation_import_zooking_no_new_reservations(mocker: MockerFixture, fake_user, test_db):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    external_reservation_id = 17
    external_property_id = 1

    # populate wrappers DB with a single reservation
    create_reservation(
        service=Service.ZOOKING,
        external_reservation_id=external_reservation_id,
        reservation_status="confirmed"
    )

    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)


    # external property 1 should be mapped in our DB aswell
    internal_property_id = set_property_internal_id(Service.ZOOKING, external_property_id)
    
    # 0 new reservations, 17 is already saved on wrappers_db
    user_reservations_response = [
        {
            "id": 17,
            "property_id": external_property_id,
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351911234567",
            "begin_datetime": "2024-05-01T12:00:00",
            "end_datetime": "2024-05-04T12:00:00",
            "cost": 150.0,
            "reservation_status": "pending",
        },
    ]


    wrapper = ZookingWrapper(queue="zooking_regular_queue")
    
    fake_user.connected_services = [wrapper.service_schema]
    message_body = to_json(MessageFactory.create_import_reservations_message(
        users=[fake_user],
    ))

    mock_requests_get = Mock()
    mock_response = Mock()
    mock_requests_get.return_value = mock_response
    mock_response.json.return_value = user_reservations_response
    mocker.patch("requests.get", mock_requests_get)

    get_reservation_external_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_reservation_by_external_id")
        
    get_property_internal_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_property_internal_id")

    create_reservations_spy = mocker.spy(Wrappers.zooking.converters.zooking_to_propertease, "create_reservation")

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    # assert
    assert get_property_internal_id_spy.call_count == 1
    call_args_property_internal = [
        call(wrapper.service_schema, external_property_id),
    ]
    get_property_internal_id_spy.assert_called_once_with(
        wrapper.service_schema, external_property_id
    )
    assert get_reservation_external_id_spy.call_count == 1
    get_reservation_external_id_spy.assert_called_once_with(
        wrapper.service_schema, 17
    )
    create_reservations_spy.call_count == 0 # no new reservations
    mock_requests_get.assert_called_once_with(
        url=wrapper.url + f"reservations/upcoming?email={fake_user.email}"
    )
    channel_mock.basic_publish.call_count == 0 # no message since no new reservations
    channel_mock.basic_ack.assert_called_once()


"""
    Test detecting a reservation passed from a confirmed/pending status to cancelled status
"""
def test_reservation_import_zooking_cancelled_reservation(mocker: MockerFixture, fake_user, test_db):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    external_reservation_id = 17
    external_property_id = 1

    # populate wrappers DB with a single reservation
    reservation_17 = create_reservation(
        service=Service.ZOOKING,
        external_reservation_id=external_reservation_id,
        reservation_status="confirmed"
    )

    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)


    # external property 1 should be mapped in our DB aswell
    internal_property_id = set_property_internal_id(Service.ZOOKING, external_property_id)
    
    # 1 new reservations and 17 status changed to canceled
    user_reservations_response = [
        {
            "id": 17,
            "property_id": external_property_id,
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351911234567",
            "begin_datetime": "2024-05-01T12:00:00",
            "end_datetime": "2024-05-04T12:00:00",
            "cost": 150.0,
            "reservation_status": "canceled",
        },
        {
            "id": 18,
            "property_id": external_property_id,
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351911234567",
            "begin_datetime": "2024-05-05T12:00:00",
            "end_datetime": "2024-05-06T12:00:00",
            "cost": 150.0,
            "reservation_status": "confirmed",
        },
    ]


    wrapper = ZookingWrapper(queue="zooking_regular_queue")
    
    fake_user.connected_services = [wrapper.service_schema]
    message_body = to_json(MessageFactory.create_import_reservations_message(
        users=[fake_user],
    ))

    mock_requests_get = Mock()
    mock_response = Mock()
    mock_requests_get.return_value = mock_response
    mock_response.json.return_value = user_reservations_response
    mocker.patch("requests.get", mock_requests_get)

    update_reservation_spy = mocker.spy(Wrappers.zooking.converters.zooking_to_propertease, "update_reservation")

    get_reservation_external_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_reservation_by_external_id")
        
    get_property_internal_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_property_internal_id")

    create_reservations_spy = mocker.spy(Wrappers.zooking.converters.zooking_to_propertease, "create_reservation")

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    expected_body = to_json(MessageFactory.create_import_reservations_response_message(wrapper.service_schema,
        [
            {
                "_id": 1,
                "reservation_status": "canceled",
                "property_id": internal_property_id,
                "owner_email": fake_user.email,
                "begin_datetime":  user_reservations_response[0].get("arrival"),
                "end_datetime":  user_reservations_response[0].get("departure"),
                "client_email": user_reservations_response[0].get("client_email"),
                "client_name": user_reservations_response[0].get("client_name"),
                "client_phone": user_reservations_response[0].get("client_phone"),
                "cost": user_reservations_response[0].get("cost"),
            },
            {
                "_id": 2,
                "reservation_status": user_reservations_response[1].get("reservation_status"),
                "property_id": internal_property_id,
                "owner_email": fake_user.email,
                "begin_datetime":  user_reservations_response[1].get("arrival"),
                "end_datetime":  user_reservations_response[1].get("departure"),
                "client_email": user_reservations_response[1].get("client_email"),
                "client_name": user_reservations_response[1].get("client_name"),
                "client_phone": user_reservations_response[1].get("client_phone"),
                "cost": user_reservations_response[1].get("cost"),
            }
        ]
    ))

    # assert
    assert get_property_internal_id_spy.call_count == 2
    call_args_property_internal = [
        call(wrapper.service_schema, external_property_id),
        call(wrapper.service_schema, external_property_id),
    ]
    assert get_property_internal_id_spy.call_args_list == call_args_property_internal
    assert get_reservation_external_id_spy.call_count == 2
    call_args_reservation_external = [
        call(wrapper.service_schema, 17),
        call(wrapper.service_schema, 18),
    ]
    assert get_reservation_external_id_spy.call_args_list == call_args_reservation_external
    create_reservations_spy.call_count == 2 # 2 new reservations
    update_reservation_spy.assert_called_once_with(
        wrapper.service_schema, reservation_17.internal_id, "canceled"
    )
    mock_requests_get.assert_called_once_with(
        url=wrapper.url + f"reservations/upcoming?email={fake_user.email}"
    )
    channel_mock.basic_publish.assert_called_once_with(
        exchange=EXCHANGE_NAME,
        routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY,
        body=expected_body,
    )
    channel_mock.basic_ack.assert_called_once()



"""
    Test receiving the import reservations message, but user is not yet connected
    to this service, so the wrapper should do nothing.
"""
def test_reservation_import_zooking_user_not_connected(mocker: MockerFixture, fake_user, test_db):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)

    wrapper = ZookingWrapper(queue="zooking_regular_queue")
    
    fake_user.connected_services = [Service.CLICKANDGO]
    message_body = to_json(MessageFactory.create_import_reservations_message(
        users=[fake_user],
    ))

    mock_requests_get = Mock()
    mocker.patch("requests.get", mock_requests_get)

    get_reservation_external_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_reservation_by_external_id")
        
    get_property_internal_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_property_internal_id")

    create_reservations_spy = mocker.spy(Wrappers.zooking.converters.zooking_to_propertease, "create_reservation")

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)


    # assert
    assert create_reservations_spy.call_count == 0
    assert mock_requests_get.call_count == 0
    channel_mock.basic_ack.assert_called_once()

"""
    Test receiving the import reservations message, but the property_id of the
    one of the new properties is invalid
"""
def test_reservation_import_zooking_invalid_property(mocker: MockerFixture, fake_user, test_db):
        # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    external_property_id = 1

    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)

    # external property 1 should be mapped in our DB aswell
    internal_property_id = set_property_internal_id(Service.ZOOKING, external_property_id)


    # 2 new reservations, but reservation 18 has an invalid property. only 17 is imported
    user_reservations_response = [
        {
            "id": 17,
            "property_id": external_property_id,
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351911234567",
            "begin_datetime": "2024-05-01T12:00:00",
            "end_datetime": "2024-05-04T12:00:00",
            "cost": 150.0,
            "reservation_status": "pending",
        },
        {
            "id": 18,
            "property_id": 999,
            "client_email": "cool_client@gmail.com",
            "client_name": "Test",
            "client_phone": "+351911234567",
            "begin_datetime": "2024-05-05T12:00:00",
            "end_datetime": "2024-05-06T12:00:00",
            "cost": 150.0,
            "reservation_status": "confirmed",
        },
    ]

    wrapper = ZookingWrapper(queue="zooking_regular_queue")
    
    fake_user.connected_services = [wrapper.service_schema]
    message_body = to_json(MessageFactory.create_import_reservations_message(
        users=[fake_user],
    ))

    mock_requests_get = Mock()
    mock_response = Mock()
    mock_requests_get.return_value = mock_response
    mock_response.json.return_value = user_reservations_response
    mocker.patch("requests.get", mock_requests_get)

    get_reservation_external_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_reservation_by_external_id")
        
    get_property_internal_id_spy = mocker.spy(Wrappers.zooking.zooking_wrapper, "get_property_internal_id")

    create_reservations_spy = mocker.spy(Wrappers.zooking.converters.zooking_to_propertease, "create_reservation")

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    expected_body = to_json(MessageFactory.create_import_reservations_response_message(wrapper.service_schema, 
        [
            {
                "_id": 1,
                "reservation_status": user_reservations_response[0].get("reservation_status"),
                "property_id": internal_property_id,
                "owner_email": fake_user.email,
                "begin_datetime":  user_reservations_response[0].get("arrival"),
                "end_datetime":  user_reservations_response[0].get("departure"),
                "client_email": user_reservations_response[0].get("client_email"),
                "client_name": user_reservations_response[0].get("client_name"),
                "client_phone": user_reservations_response[0].get("client_phone"),
                "cost": user_reservations_response[0].get("cost"),
            },
        ]
    ))

    # assert
    assert get_property_internal_id_spy.call_count == 2
    call_args_property_internal = [
        call(wrapper.service_schema, external_property_id),
        call(wrapper.service_schema, 999),
    ]
    assert get_property_internal_id_spy.call_args_list == call_args_property_internal
    get_reservation_external_id_spy.assert_called_once_with(
        wrapper.service_schema, 17
    )
    create_reservations_spy.assert_called_once_with(
        wrapper.service_schema, 17, user_reservations_response[0].get("reservation_status")
    )
    mock_requests_get.assert_called_once_with(
        url=wrapper.url + f"reservations/upcoming?email={fake_user.email}"
    )
    channel_mock.basic_publish.assert_called_once_with(
        exchange=EXCHANGE_NAME,
        routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY,
        body=expected_body,
    )
    channel_mock.basic_ack.assert_called_once()
