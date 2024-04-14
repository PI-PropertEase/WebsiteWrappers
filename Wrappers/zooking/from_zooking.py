from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME, WRAPPER_TO_CALENDAR_ROUTING_KEY
from ProjectUtils.MessagingService.schemas import (
    MessageFactory,
    MessageType,
    to_json,
)
import json
import hashlib
import requests
from time import sleep
from datetime import datetime
from pydantic import BaseModel

cachedReservations = dict()
mapping_externalServiceId_propertyServiceId = dict()


class Reservation(BaseModel):
    id: int
    property_id: int
    status: str
    begin_datetime: str
    end_datetime: str
    client_name: str
    client_phone: str
    cost: float
    service: str = "zooking"


def dict_to_model(reservation_id, reservation, message_type):
    reservation_model = Reservation(
        property_id=reservation['property_id'],
        status=reservation['status'],
        client_name=reservation['client_name'],
        client_phone=reservation['client_phone'],
        begin_datetime=reservation['arrival'],
        end_datetime=reservation['departure'],
        cost=reservation['cost'],
        id=insert_property_service_id_from_external_service_id(reservation_id)
    )
    return MessageFactory.create_reservation_message(message_type, reservation_model)


def get_reservation_by_id(reservations: dict, reservation_id: int):
    for reservation in reservations:
        if reservation['id'] == reservation_id:
            return reservation
    return None


# TODO alter this later
def insert_property_service_id_from_external_service_id(external_id: int):
    property_id = external_id * 2
    mapping_externalServiceId_propertyServiceId[external_id] = property_id
    return property_id


def run():
    reservations = requests.get(
        url="http://localhost:8000/reservations?email=joao.dourado1@gmail.com").json()  # TODO: Remove hardcoded email
    global cachedReservations

    reservations_dict = {reservation["id"]: reservation for reservation in reservations}
    if hashlib.md5(str(cachedReservations).encode()).hexdigest() != hashlib.md5(
            str(reservations_dict).encode()).hexdigest():
        for reservation_id in reservations_dict:
            if reservation_id not in cachedReservations:
                body = dict_to_model(reservation_id, reservations_dict[reservation_id], MessageType.RESERVATION_CREATE)
            elif reservation_id not in reservations_dict:
                body = dict_to_model(reservation_id, cachedReservations[reservation_id], MessageType.RESERVATION_DELETE)
            elif hashlib.md5(str(cachedReservations[reservation_id]).encode()).hexdigest() != hashlib.md5(
                    str(reservations_dict[reservation_id]).encode()).hexdigest():
                body = dict_to_model(reservation_id, reservations_dict[reservation_id], MessageType.RESERVATION_UPDATE)

            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY, body=to_json(body))
        cachedReservations = reservations_dict
        print("new cache:\n")
        print(cachedReservations)
    else:
        print("No changes (cache hit)")


while True:
    run()
    sleep(30)
