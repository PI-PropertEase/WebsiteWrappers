from ProjectUtils.MessagingService.queue_definitions import channel, EXCHANGE_NAME, WRAPPER_TO_CALENDAR_ROUTING_KEY
from ProjectUtils.MessagingService.schemas import (
    MessageFactory,
    MessageType,
    to_json, Service,
)
import json
import hashlib
import requests
from time import sleep
from datetime import datetime
from pydantic import BaseModel

cachedReservations = {}


class Reservation(BaseModel):
    id: int
    property_id: int
    status: str
    client_name: str
    client_phone: str
    begin_datetime: datetime
    end_datetime: datetime
    cost: float
    service: Service = Service.ZOOKING


def dict_to_reservation_model(reservation_id, reservation):
    return Reservation(
        property_id=reservation['property_id'],
        status=reservation['status'],
        client_name=reservation['client_name'],
        client_phone=reservation['client_phone'],
        begin_datetime=reservation['arrival'],
        end_datetime=reservation['departure'],
        cost=reservation['cost'],
        id=reservation_id # TODO adicionar aqui mapeamento de id para reservas (!= do para propriedades)
    )


def run():
    reservations = requests.get(
        url="http://localhost:8000/reservations?email=alicez@gmail.com").json()  # TODO: Remove hardcoded email
    global cachedReservations

    reservations_dict = {reservation["id"]: reservation for reservation in reservations}
    created_reservations = []
    updated_reservations = []
    deleted_reservations = []

    if hashlib.md5(str(cachedReservations).encode()).hexdigest() != hashlib.md5(str(reservations_dict).encode()).hexdigest():
        print("A change occured (cache miss)")
        for reservation_id in reservations_dict:
            if reservation_id not in cachedReservations:
                created_reservations.append(dict_to_reservation_model(reservation_id, reservations_dict[reservation_id]))
            elif reservation_id not in reservations_dict:
                deleted_reservations.append(dict_to_reservation_model(reservation_id, cachedReservations[reservation_id]))
            elif hashlib.md5(str(cachedReservations[reservation_id]).encode()).hexdigest() != hashlib.md5(
                    str(reservations_dict[reservation_id]).encode()).hexdigest():
                updated_reservations.append(dict_to_reservation_model(reservation_id, reservations_dict[reservation_id]))

        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY, body=to_json(MessageFactory.create_reservation_message()))
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY, body=to_json(body))
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=WRAPPER_TO_CALENDAR_ROUTING_KEY, body=to_json(body))
        cachedReservations = reservations_dict
        print("new cache:\n")
        print(cachedReservations)
    else:
        print("No changes (cache hit)")


while True:
    run()
    sleep(30)
