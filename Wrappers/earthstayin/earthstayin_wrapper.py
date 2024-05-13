from datetime import datetime

import requests

from .converters.earthstayin_to_propertease import EarthstayinToPropertease
from .converters.propertease_to_earthstayin import ProperteaseToEarthstayin
from ..base_wrapper.wrapper import BaseWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_EARTHSTAYIN_ROUTING_KEY, WRAPPER_BROADCAST_ROUTING_KEY,
)
from ..models import Service, ReservationStatus
from .. import crud


class EarthStayinWrapper(BaseWrapper):
    def __init__(self, queue: str) -> None:
        super().__init__(
            url="http://localhost:8001/",
            queue=queue,
            service_schema=Service.EARTHSTAYIN,
        )
        earthstayin_queue = channel.queue_declare(queue=self.queue, durable=True)
        channel.queue_bind(
            queue=earthstayin_queue.method.queue,
            exchange=EXCHANGE_NAME,
            routing_key=WRAPPER_EARTHSTAYIN_ROUTING_KEY,
        )
        channel.queue_bind(
            queue=earthstayin_queue.method.queue,
            exchange=EXCHANGE_NAME,
            routing_key=WRAPPER_BROADCAST_ROUTING_KEY,
        )

    def create_property(self, property):
        url = self.url + "properties"
        print("Creating property...")
        requests.post(url=url, json=property)

    def update_property(self, prop_internal_id: int, prop_update_parameters: dict):
        external_id = crud.get_property_external_id(self.service_schema, prop_internal_id)
        url = self.url + f"properties/{external_id}"
        print("Updating property...")
        print("internal_id", prop_internal_id, "external_id", external_id)
        print("update_parameters", prop_update_parameters)
        requests.put(url=url, json=ProperteaseToEarthstayin.convert_property(prop_update_parameters))

    def delete_property(self, property):
        _id = property.get("id")
        print("Deleting property...")
        url = self.url + f"properties/{_id}"
        requests.delete(url=url)

    def create_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: str,
                                end_datetime: str):

        external_id = crud.get_property_external_id(self.service_schema, property_internal_id)
        if external_id is None:
            print(f"Property with internal_id {property_internal_id} not found in IdMapper database.")
            return

        url = self.url + "properties/closedtimeframes"
        print("Creating management event...")
        print("THIS IS THE BODY", {
            "property_id": external_id,
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        })
        response = requests.post(url=url, json={
            "property_id": external_id,
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        })
        if response.status_code == 200:
            print("Success creating management event")
            crud.create_management_event(self.service_schema, event_internal_id, response.json()["id"])
        else:
            print("Failed creating management event", response.json())

    def update_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: str,
                                end_datetime: str):
        if crud.get_property_external_id(self.service_schema, property_internal_id) is None:
            print(f"Property with internal_id {property_internal_id} not found in IdMapper database.")
            return

        event = crud.get_management_event(self.service_schema, event_internal_id)
        if event is None:
            print(f"External counterpart of management event with internal_id {event_internal_id} not found.")
            return
        event_external_id = event.external_id
        url = self.url + f"properties/closedtimeframes/{event_external_id}"
        print("Updating management event...")
        response = requests.put(url=url, json={
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        })
        if response.status_code == 200:
            print("Success updating management event")
        else:
            print("Failed updating management event", response.json())

    def delete_management_event(self, property_internal_id: int, event_internal_id: int):
        if crud.get_property_external_id(self.service_schema, property_internal_id) is None:
            print(f"Property with internal_id {property_internal_id} not found in IdMapper database.")
            return

        event = crud.get_management_event(self.service_schema, event_internal_id)
        if event is None:
            print(f"External counterpart of management event with internal_id {event_internal_id} not found.")
            return
        event_external_id = event.external_id
        url = self.url + f"properties/closedtimeframes/{event_external_id}"
        print("Deleting management event...")
        response = requests.delete(url=url)
        if response.status_code == 204:
            print("Success deleting management event")
            crud.delete_management_event(self.service_schema, event_internal_id)
        else:
            print("Failed deleting management event", response.json())

    def import_properties(self, user):
        url = self.url + "properties?email=" + user.get("email")
        print("Importing properties...")
        earthstayin_properties = requests.get(url=url).json()
        converted_properties = [
            EarthstayinToPropertease.convert_property(p) for p in earthstayin_properties
        ]
        return converted_properties

    def import_reservations(self, user):
        email = user.get("email")
        url = self.url + "reservations?email=" + email
        print("Importing reservations...")
        earthsayin_reservations = requests.get(url=url).json()
        converted_properties = [
            EarthstayinToPropertease.convert_reservation(r, email) for r in earthsayin_reservations
        ]
        return converted_properties

    def import_new_or_newly_canceled_reservations(self, user):
        email = user.get("email")
        url = f"{self.url}reservations/upcoming?email={email}"
        print("Importing new reservations...")
        earthsayin_reservations = requests.get(url=url).json()
        converted_reservations = [
            EarthstayinToPropertease.convert_reservation(r, email, reservation)
            for r in earthsayin_reservations
            if crud.get_property_internal_id(self.service_schema, r["property_id"]) is not None and
               ((reservation := crud.get_reservation_by_external_id(self.service_schema, r["id"])) is None or
                (r[
                     "reservation_status"] == "canceled" and reservation.reservation_status != ReservationStatus.CANCELED))
        ]
        return converted_reservations

    def confirm_reservation(self, reservation_internal_id: int, property_internal_id: int, begin_datetime: str,
                            end_datetime: str):
        _id = crud.get_reservation_external_id(self.service_schema, reservation_internal_id)
        if _id is not None:
            # if reservation made on this service
            url = self.url + f"reservations/{_id}"
            print("Confirming reservation...", reservation_internal_id)
            response = requests.put(url=url, json={"reservation_status": "confirmed"})
            if response.status_code == 200:
                crud.update_reservation(self.service_schema, reservation_internal_id,
                                        response.json()["reservation_status"])
            else:
                print("Error confirming reservation")
        else:
            print("Creating already confirmed reservation as an event...", reservation_internal_id)
            self.create_management_event(property_internal_id, reservation_internal_id, begin_datetime, end_datetime)

    def cancel_overlapping_reservation(self, reservation_internal_id: int):
        _id = crud.get_reservation_external_id(self.service_schema, reservation_internal_id)
        if _id is not None:
            # if it's receiving this message, reservation was already made in this service
            url = self.url + f"reservations/{_id}"
            print("Cancelling reservation...", reservation_internal_id)
            response = requests.put(url=url, json={"reservation_status": "canceled"})
            if response.status_code == 200:
                crud.update_reservation(self.service_schema, reservation_internal_id, response.json()["reservation_status"])
            else:
                print("Error cancelling reservation")
        else:
            print("Error reservation to cancel doesn't exist")

    def cancel_reservation(self, reservation_internal_id: int, property_internal_id: int):
        _id = crud.get_reservation_external_id(self.service_schema, reservation_internal_id)
        if _id is not None:
            # if reservation made on this service
            url = self.url + f"reservations/{_id}"
            print("Cancelling reservation...", reservation_internal_id)
            response = requests.put(url=url, json={"reservation_status": "canceled"})
            if response.status_code == 200:
                crud.update_reservation(self.service_schema, reservation_internal_id, response.json()["reservation_status"])
            else:
                print("Error cancelling reservation")
        else:
            print("Deleting event corresponding to that reservation", reservation_internal_id)
            self.delete_management_event(property_internal_id, reservation_internal_id)
