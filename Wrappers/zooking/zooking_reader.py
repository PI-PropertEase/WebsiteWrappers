from ProjectUtils.MessagingService.queue_definitions import w2a_channel, API_EXCHANGE
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

cachedReservations = {}

class Reservation(BaseModel):
    id: int
    property_id: int
    status: str
    client_name: str
    client_phone: str
    arrival: str
    departure: str
    cost: float

def dict_to_model(id, reservation, message_type):
    reservation_model= Reservation(
        property_id=reservation['property_id'],
        status=reservation['status'],
        client_name=reservation['client_name'],
        client_phone=reservation['client_phone'],
        arrival=reservation['arrival'],
        departure=reservation['departure'],
        cost=reservation['cost'],
        id=id
    )
    return MessageFactory.create_reservation_message(message_type, reservation_model)

def run():
    reservations = requests.get(url="http://localhost:8000/reservations").json()
    global cachedReservations

    if hashlib.md5(str(cachedReservations).encode()).hexdigest() != hashlib.md5(str(reservations).encode()).hexdigest():
        print("A change occured (cache miss)")
        all_ids = set(list(reservations.keys()) + list(cachedReservations.keys()))
        for reservation_id in all_ids:
            if reservation_id not in cachedReservations:
                body = dict_to_model(reservation_id, reservations[reservation_id], MessageType.RESERVATION_CREATE)
            elif reservation_id not in reservations:
                body = dict_to_model(reservation_id, cachedReservations[reservation_id], MessageType.RESERVATION_DELETE)
            elif hashlib.md5(str(cachedReservations[reservation_id]).encode()).hexdigest() != hashlib.md5(str(reservations[reservation_id]).encode()).hexdigest():
                body = dict_to_model(reservation_id, reservations[reservation_id], MessageType.RESERVATION_UPDATE)

        w2a_channel.basic_publish(exchange=API_EXCHANGE, routing_key="", body=to_json(body))
        cachedReservations = reservations
        print("new cache:\n")
        print(cachedReservations)
    else:
        print("No changes (cache hit)")

while True:
    run()
    sleep(30)
