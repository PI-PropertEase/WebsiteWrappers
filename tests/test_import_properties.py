import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, Mock
from Wrappers.regular_events_handler import handle_recv
from Wrappers.zooking.zooking_wrapper import ZookingWrapper
from Wrappers.clickandgo.clickandgo_wrapper import CNGWrapper
from Wrappers.earthstayin.earthstayin_wrapper import EarthStayinWrapper
from Wrappers.zooking.converters.zooking_to_propertease import ZookingToPropertease
from Wrappers.clickandgo.converters.clickandgo_to_propertease import ClickandgoToPropertease
from Wrappers.earthstayin.converters.earthstayin_to_propertease import EarthstayinToPropertease
from ProjectUtils.MessagingService.schemas import MessageFactory, to_json
from ProjectUtils.MessagingService.queue_definitions import (
    EXCHANGE_NAME,
    WRAPPER_TO_APP_ROUTING_KEY,
)
from fixtures import fake_user, test_db


"""
    Testing that receiving the IMPORT_PROPERTIES message triggers a basic_publish
    with the same data that was imported but converted to propertease format, and 
    that the database function to create a mapping is called.
"""


def test_import_properties_zooking_receive_message_return_properties(mocker: MockerFixture, fake_user, test_db):
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

    def fake_internal_id(*args, **kwargs):
        return args[1] * 2      # 2 * property_external_id
    
    mock_set_property_internal_id = MagicMock()
    mock_set_property_internal_id.side_effect = fake_internal_id
    mocker.patch("Wrappers.zooking.converters.zooking_to_propertease.set_property_internal_id", mock_set_property_internal_id)
    
    mock_requests_get = Mock()
    mock_response = Mock()
    mock_requests_get.return_value = mock_response
    mock_response.json.return_value = user_properties_response
    mocker.patch("requests.get", mock_requests_get)
    
    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    expected_body = to_json(MessageFactory.create_import_properties_response_message(
        service=wrapper.service_schema, properties=[ZookingToPropertease.convert_property(prop) for prop in user_properties_response]
    ))

    # asserts
    assert mock_set_property_internal_id.call_count == 4    # 2 times in the actual code, 2 times in the tests
    mock_requests_get.assert_called_once_with(url=wrapper.url + "properties?email=cool_guy@gmail.com")
    channel_mock.basic_publish.assert_called_once_with(
        exchange=EXCHANGE_NAME,
        routing_key=WRAPPER_TO_APP_ROUTING_KEY,
        body=expected_body,
    )
    channel_mock.basic_ack.assert_called_once()


def test_import_properties_clickandgo_receive_message_return_properties(mocker: MockerFixture, fake_user, test_db):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    wrapper = CNGWrapper(queue="clickandgo_regular_queue")
    message_body = to_json(MessageFactory.create_import_properties_message(fake_user))

    user_properties_response = [
        {"user_email":"joao.p.dourado1@gmail.com","name":"Cool house 🦼🛹","address":"Morada Miguel","curr_price":22.0,"description":"Interesting house","guest_num":5,"house_area":200,"bedrooms":{"bedroom_1":[{"number_beds":2,"bed_type":"king"},{"number_beds":1,"bed_type":"single"},{"number_beds":1,"bed_type":"queen"},{"number_beds":1,"bed_type":"twin"}]},"bathrooms":[{"bathroom_fixtures":["toilet","tub","shower"]}],"available_amenities":["AC","patio","wifi_free","parking"],"house_rules":{"check_in":"16:00-23:59","check_out":"00:00-10:00","smoking_allowed":False,"parties_allowed":True,"rest_time":"22:00-08:00","pets_allowed":True},"additional_info":"Somos fixes","cancellation_policy":"Não há reembolsos","house_manager":{"name":"Alice Zqt","phone_number":"+351920920920","languages":["Portuguese","English"]},"id":11},
        {"user_email":"joao.p.dourado1@gmail.com","name":"Não é a mesma casa 😎","address":"Morada no meio do mato","curr_price":22.0,"description":"Interesting house","guest_num":5,"house_area":200,"bedrooms":{"bedroom_1":[{"number_beds":2,"bed_type":"king"},{"number_beds":1,"bed_type":"single"},{"number_beds":1,"bed_type":"queen"},{"number_beds":1,"bed_type":"twin"}]},"bathrooms":[{"bathroom_fixtures":["toilet","tub","shower"]}],"available_amenities":["AC","patio","wifi_free","parking"],"house_rules":{"check_in":"16:00-23:59","check_out":"00:00-10:00","smoking_allowed":False,"parties_allowed":True,"rest_time":"22:00-08:00","pets_allowed":True},"additional_info":"Somos fixes","cancellation_policy":"Não há reembolsos","house_manager":{"name":"Alice Zqt","phone_number":"+351920920920","languages":["Portuguese","English"]},"id":12}
    ]

    def fake_internal_id(*args, **kwargs):
        return args[1] * 2      # 2 * property_external_id
    
    mock_set_property_internal_id = MagicMock()
    mock_set_property_internal_id.side_effect = fake_internal_id
    mocker.patch("Wrappers.clickandgo.converters.clickandgo_to_propertease.set_property_internal_id", mock_set_property_internal_id)
    
    mock_requests_get = Mock()
    mock_response = Mock()
    mock_requests_get.return_value = mock_response
    mock_response.json.return_value = user_properties_response
    mocker.patch("requests.get", mock_requests_get)
    
    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    expected_body = to_json(MessageFactory.create_import_properties_response_message(
        service=wrapper.service_schema, properties=[ClickandgoToPropertease.convert_property(prop) for prop in user_properties_response]
    ))

    # asserts
    assert mock_set_property_internal_id.call_count == 4    # 2 times in the actual code, 2 times in the tests
    mock_requests_get.assert_called_once_with(url=wrapper.url + "properties?email=cool_guy@gmail.com")
    channel_mock.basic_publish.assert_called_once_with(
        exchange=EXCHANGE_NAME,
        routing_key=WRAPPER_TO_APP_ROUTING_KEY,
        body=expected_body,
    )
    channel_mock.basic_ack.assert_called_once()



def test_import_properties_earthstayin_receive_message_return_properties(mocker: MockerFixture, fake_user, test_db):
    # mock/setup test
    channel_mock = MagicMock()
    method_mock = MagicMock()
    properties_mock = MagicMock()

    wrapper = EarthStayinWrapper(queue="earthstayin_regular_queue")
    message_body = to_json(MessageFactory.create_import_properties_message(fake_user))

    user_properties_response = [
        {"user_email":"joao.p.dourado1@gmail.com","name":"Conforto e Bem Estar","address":"Rua 91011","curr_price":400.0,"description":"A residência mais confortável","number_of_guests":4,"square_meters":2000,"bedrooms":{"bedroom_1":[{"number_beds":1,"bed_type":"single_bed"},{"number_beds":1,"bed_type":"king_bed"}],"bedroom_2":[{"number_beds":1,"bed_type":"queen_bed"}]},"bathrooms":[{"name":"bathroom_groundfloor","bathroom_fixtures":["toilet","tub","shower","bidet"]}],"amenities":["AC","free_wifi","car_parking"],"accessibilities":["ramp"],"additional_info":"Recebem um rebuçado","house_rules":{"checkin_time":"14:30-23:59","checkout_time":"00:00-11:30","smoking_allowed":True,"rest_time":"22:30","pets_allowed":True},"id":11},
        {"user_email":"joao.p.dourado1@gmail.com","name":"Very cool home!","address":"Rua 2002","curr_price":33.0,"description":"A residência mais confortável","number_of_guests":4,"square_meters":2000,"bedrooms":{"bedroom_1":[{"number_beds":1,"bed_type":"single_bed"},{"number_beds":1,"bed_type":"king_bed"}],"bedroom_2":[{"number_beds":1,"bed_type":"queen_bed"},{"number_beds":1,"bed_type":"twin_bed"}]},"bathrooms":[{"name":"bathroom_groundfloor","bathroom_fixtures":["toilet","tub","shower","bidet"]}],"amenities":["AC","free_wifi","car_parking"],"accessibilities":["ramp"],"additional_info":"Recebem um rebuçado","house_rules":{"checkin_time":"14:30-23:59","checkout_time":"00:00-11:30","smoking_allowed":True,"rest_time":"22:30","pets_allowed":True},"id":12}
    ]

    def fake_internal_id(*args, **kwargs):
        return args[1] * 2      # 2 * property_external_id
    
    mock_set_property_internal_id = MagicMock()
    mock_set_property_internal_id.side_effect = fake_internal_id
    mocker.patch("Wrappers.earthstayin.converters.earthstayin_to_propertease.set_property_internal_id", mock_set_property_internal_id)
    
    mock_requests_get = Mock()
    mock_response = Mock()
    mock_requests_get.return_value = mock_response
    mock_response.json.return_value = user_properties_response
    mocker.patch("requests.get", mock_requests_get)
    
    mocker.patch("ProjectUtils.MessagingService.schemas.time", return_value=1)

    # act
    handle_recv(channel_mock, method_mock, properties_mock, message_body, wrapper)

    expected_body = to_json(MessageFactory.create_import_properties_response_message(
        service=wrapper.service_schema, properties=[EarthstayinToPropertease.convert_property(prop) for prop in user_properties_response]
    ))

    # asserts
    assert mock_set_property_internal_id.call_count == 4    # 2 times in the actual code, 2 times in the tests
    mock_requests_get.assert_called_once_with(url=wrapper.url + "properties?email=cool_guy@gmail.com")
    channel_mock.basic_publish.assert_called_once_with(
        exchange=EXCHANGE_NAME,
        routing_key=WRAPPER_TO_APP_ROUTING_KEY,
        body=expected_body,
    )
    channel_mock.basic_ack.assert_called_once()

