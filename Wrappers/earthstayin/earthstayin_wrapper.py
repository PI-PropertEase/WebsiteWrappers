from datetime import datetime

import requests
import logging

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


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class EarthStayinWrapper(BaseWrapper):
    def __init__(self, queue: str) -> None:
        super().__init__(
            url="http://host.docker.internal:8001/",
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
        LOGGER.info("Creating property in Earthstayin external API: %s", property)
        requests.post(url=url, json=property)

    def update_property(self, prop_internal_id: int, prop_update_parameters: dict):
        external_id = crud.get_property_external_id(self.service_schema, prop_internal_id)
        url = self.url + f"properties/{external_id}"
        LOGGER.info("Updating property in Earthstayin external API. Internal_id - '%s'; External_id - '%s'. Update parameters: %s", prop_internal_id, external_id, prop_update_parameters)
        requests.put(url=url, json=ProperteaseToEarthstayin.convert_property(prop_update_parameters))

    def delete_property(self, property):
        _id = property.get("id")
        LOGGER.info("Deleting property in Earthstayin external API: %s", property)
        url = self.url + f"properties/{_id}"
        requests.delete(url=url)

    def create_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: str,
                                end_datetime: str):
        LOGGER.info("Creating Management Event in Earthstayin external API for property_internal_id '%s': Event_internal_id - '%s'; Begin_datetime - '%s'; End_datetime - '%s'", 
                    property_internal_id, event_internal_id, begin_datetime, end_datetime)
        external_id = crud.get_property_external_id(self.service_schema, property_internal_id)
        if external_id is None:
            print(f"Property with internal_id {property_internal_id} not found in IdMapper database.")
            return

        url = self.url + "properties/closedtimeframes"
        LOGGER.info("POST request call (create management event) in Earthstayin API at '%s'...", url)
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
            LOGGER.info("Successfully created management event with internal_id '%s'", event_internal_id)
            crud.create_management_event(self.service_schema, event_internal_id, response.json()["id"])
        else:
            LOGGER.error("Failed creating management event. Response: %s", response.content)

    def update_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: str,
                                end_datetime: str):
        LOGGER.info("Updating Management Event in Earthstayin external API for property_internal_id '%s': Event_internal_id - '%s'; Begin_datetime - '%s'; End_datetime - '%s'", 
                    property_internal_id, event_internal_id, begin_datetime, end_datetime)
        if crud.get_property_external_id(self.service_schema, property_internal_id) is None:
            LOGGER.error("Property with internal_id %s not found in IdMapper database.", property_internal_id)
            return

        event = crud.get_management_event(self.service_schema, event_internal_id)
        if event is None:
            LOGGER.error("External counterpart of management event with internal_id '%s' not found.", event_internal_id)
            return
        event_external_id = event.external_id
        url = self.url + f"properties/closedtimeframes/{event_external_id}"
        LOGGER.info("PUT request call (to update management event) in Earthstayin API at '%s'...", url)
        response = requests.put(url=url, json={
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        })
        if response.status_code == 200:
            LOGGER.info("Successfully updated management event with internal_id '%s'", event_internal_id)
        else:
            LOGGER.error("Failed updating management event. Response: %s", response.content)

    def delete_management_event(self, property_internal_id: int, event_internal_id: int):
        LOGGER.info("Deleting Management Event in Earthstayin external API for property_internal_id '%s': Event_internal_id - '%s'", 
                    property_internal_id, event_internal_id)
        if crud.get_property_external_id(self.service_schema, property_internal_id) is None:
            LOGGER.error("Property with internal_id %s not found in IdMapper database.", property_internal_id)
            return

        event = crud.get_management_event(self.service_schema, event_internal_id)
        if event is None:
            LOGGER.error("External counterpart of management event with internal_id '%s' not found.", event_internal_id)
            return
        event_external_id = event.external_id
        url = self.url + f"properties/closedtimeframes/{event_external_id}"
        LOGGER.info("DELETE request call in Earthstayin API at '%s'... Deleting event_external_id '%s'", 
                    url, event_external_id)
        response = requests.delete(url=url)
        if response.status_code == 204:
            LOGGER.info("Successfully deleted management event with internal_id '%s'", event_internal_id)
            crud.delete_management_event(self.service_schema, event_internal_id)
        else:
            LOGGER.error("Failed deleting management event. Response: %s", response.content)

    def import_properties(self, user):
        email = user.get("email")
        url = self.url + "properties?email=" + email
        LOGGER.info("Importing Earthstayin reservations for user '%s'", email)
        LOGGER.info("GET request call in Earthstayin API at '%s'..", url)
        earthstayin_properties = requests.get(url=url).json()
        converted_properties = [
            EarthstayinToPropertease.convert_property(p) for p in earthstayin_properties
        ]
        return converted_properties

    def import_reservations(self, user):
        email = user.get("email")
        url = self.url + "reservations?email=" + email
        LOGGER.info("Importing Earthstayin reservations for user '%s'", email)
        LOGGER.info("GET request call in Earthstayin API at '%s'..", url)
        earthsayin_reservations = requests.get(url=url).json()
        converted_properties = [
            EarthstayinToPropertease.convert_reservation(r, email) for r in earthsayin_reservations
        ]
        return converted_properties

    def import_new_or_newly_canceled_reservations(self, user):
        email = user.get("email")
        url = f"{self.url}reservations/upcoming?email={email}"
        LOGGER.info("Importing Earthstayin NEW or NEWLY CANCELLED reservations for user '%s'", email)
        LOGGER.info("GET request call in Earthstayin API at '%s'...", url)
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

    def import_new_properties(self, user):
        email = user.get("email")
        LOGGER.info("Importing Earthstayin NEW properties for user '%s'", email)
        url = f"{self.url}properties?email={email}"
        LOGGER.info("GET request call in Earthstayin API at '%s'...", url)
        response = requests.get(url=url)
        if response.status_code == 200:
            earthstayin_properties = response.json()
            # import properties that don't exist -> not mapped in our database
            converted_properties = [
                EarthstayinToPropertease.convert_property(prop)
                for prop in earthstayin_properties
                if (crud.get_property_internal_id(self.service_schema, prop.get("id")) is None)
            ]
            return converted_properties
        LOGGER.error("Importing new properties failed with status code %s. Response: %s", response.status_code, response.content)
        return []

