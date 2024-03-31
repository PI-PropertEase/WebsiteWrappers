from ProjectUtils.MessagingService.queue_definitions import w2a_channel, WRAPPER_TO_APP_QUEUE
from ProjectUtils.MessagingService.schemas import ReservationType
import json
import hashlib
import requests

cachedReservations = {}

def send_msg(channel, method, properties, body):
    pass

def run():
    reservations = requests.get(url="http://localhost:8000/reservations").json()
    global cachedReservations

    if hashlib.md5(str(cachedReservations).encode()).hexdigest() != hashlib.md5(str(reservations).encode()).hexdigest():
        for reservation_id in reservations.keys():
            if reservation_id not in cachedReservations:
                pass
        cachedReservations = reservations


run()
run()
