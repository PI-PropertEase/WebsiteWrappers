from datetime import datetime

import requests
import logging

from Wrappers.zooking.converters.propertease_to_zooking import ProperteaseToZooking
from Wrappers.zooking.converters.zooking_to_propertease import ZookingToPropertease
from ..base_wrapper.wrapper import BaseWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_ZOOKING_ROUTING_KEY, WRAPPER_BROADCAST_ROUTING_KEY,
)
from .. import crud
from ..models import Service, ReservationStatus

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class ZookingWrapper(BaseWrapper):
    def __init__(self, queue: str) -> None:
        super().__init__(
            url="http://host.docker.internal:8000/",
            queue=queue,
            service_schema=Service.ZOOKING,
        )
        zooking_queue = channel.queue_declare(queue=self.queue, durable=True)
        channel.queue_bind(
            queue=zooking_queue.method.queue,
            exchange=EXCHANGE_NAME,
            routing_key=WRAPPER_ZOOKING_ROUTING_KEY,
        )
        channel.queue_bind(
            queue=zooking_queue.method.queue,
            exchange=EXCHANGE_NAME,
            routing_key=WRAPPER_BROADCAST_ROUTING_KEY,
        )

    def create_property(self, property):
        url = self.url + "properties"
        LOGGER.info("Creating property in Zooking external API: %s", property)
        requests.post(url=url, json=property)

    def update_property(self, prop_internal_id: int, prop_update_parameters: dict):
        external_id = crud.get_property_external_id(self.service_schema, prop_internal_id)
        url = self.url + f"properties/{external_id}"
        LOGGER.info("Updating property in Zooking external API. Internal_id - '%s'; External_id - '%s'. Update parameters: %s", prop_internal_id, external_id, prop_update_parameters)
        response = requests.put(url=url, json=ProperteaseToZooking.convert_property(prop_update_parameters))
        return response

    def delete_property(self, property):
        _id = property.get("id")
        LOGGER.info("Deleting property in Zooking external API: %s", property)
        url = self.url + f"properties/{_id}"
        requests.delete(url=url)

    def create_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: str,
                                end_datetime: str):
        LOGGER.info("Creating Management Event in Zooking external API for property_internal_id '%s': Event_internal_id - '%s'; Begin_datetime - '%s'; End_datetime - '%s'", 
                    property_internal_id, event_internal_id, begin_datetime, end_datetime)
        external_id = crud.get_property_external_id(self.service_schema, property_internal_id)
        if external_id is None:
            LOGGER.error("Trying to create a management event for a non-existing property with internal_id '%s'", property_internal_id)
            return

        url = self.url + f"properties/{external_id}"
        update_parameters = {"closed_time_frames": [{
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        }]}
        LOGGER.info("PUT request call (to create management event for property_external_id '%s') in Zooking API at '%s'...", external_id, url)
        response = requests.put(url=url, json=ProperteaseToZooking.convert_property(update_parameters))
        # TODO implement check against different status codes later
        if response.status_code == 200:
            LOGGER.info("Success created management event...")
            updated_property = response.json()
            returned_closed_time_frames = updated_property["closed_time_frames"]
            for management_event_id, management_event in returned_closed_time_frames.items():
                if (management_event["begin_datetime"] == begin_datetime and
                        management_event["end_datetime"] == end_datetime):
                    # management_event_id is the external id
                    crud.create_management_event(self.service_schema, event_internal_id, management_event_id)
                    break
        else:
            LOGGER.error("Failed creating management event for property_internal_id '%s'. Response data: ", response.content)

    def update_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: str,
                                end_datetime: str):
        LOGGER.info("Updating Management Event in Zooking external API for property_internal_id '%s': Event_internal_id - '%s'; Begin_datetime - '%s'; End_datetime - '%s'", 
                    property_internal_id, event_internal_id, begin_datetime, end_datetime)

        external_id = crud.get_property_external_id(self.service_schema, property_internal_id)
        if external_id is None:
            LOGGER.error("Trying to update a management event for a non-existing property with internal_id '%s'", property_internal_id)
            return

        url = self.url + f"properties/{external_id}"
        update_parameters = {"closed_time_frames": [{
            "id": crud.get_management_event(self.service_schema, event_internal_id).external_id,
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        }]}
        LOGGER.info("PUT request call (to update management event for property_external_id '%s') in Zooking API at '%s'...", external_id, url)
        response = requests.put(url=url, json=ProperteaseToZooking.convert_property(update_parameters))
        if response.status_code == 200:
            LOGGER.info("Successfully updated management event")
        else:
            LOGGER.error("Failed updating management event. Response: '%s'", response.content)
        # TODO implement check against different status codes later
        # don't need to update anything on the mappers

    def delete_management_event(self, property_internal_id: int, event_internal_id: int):
        LOGGER.info("Deleting Management Event in Zooking external API for property_internal_id '%s': Event_internal_id - '%s'", 
                    property_internal_id, event_internal_id)

        external_id = crud.get_property_external_id(self.service_schema, property_internal_id)
        if external_id is None:
            LOGGER.error("Trying to delete a management event for a non-existing property with internal_id '%s'", property_internal_id)
            return

        url = self.url + f"properties/{external_id}"
        event_external_id = crud.get_management_event(self.service_schema, event_internal_id).external_id
        update_parameters = {"closed_time_frames": [{
            "id": event_external_id,
        }]}
        LOGGER.info("PUT request call (to delete management event for property_external_id '%s') in Zooking API at '%s'... Deleting event_external_id '%s'", 
                    external_id, url, event_external_id)
        response = requests.put(url=url, json=ProperteaseToZooking.convert_property(update_parameters))
        # TODO implement check against different status codes later
        if response.status_code == 200:
            LOGGER.info("Successfully deleted management event")
            crud.delete_management_event(self.service_schema, event_internal_id)
        else:
            LOGGER.error("Failed to delete management event. Response: '%s'", response.content)

    def import_properties(self, user):
        email = user.get("email")
        url = self.url + "properties?email=" + email
        LOGGER.info("Importing Zooking properties for user '%s'", email)
        LOGGER.info("GET request call in Zooking API at '%s'", url)
        zooking_properties = requests.get(url=url).json()
        converted_properties = [
            ZookingToPropertease.convert_property(p) for p in zooking_properties
        ]
        return converted_properties

    def import_reservations(self, user):
        email = user.get("email")
        url = self.url + "reservations?email=" + email
        LOGGER.info("Importing Zooking reservations for user '%s'", email)
        LOGGER.info("GET request call in Zooking API at '%s'..", url)
        zooking_reservations = requests.get(url=url).json()
        converted_reservations = [
            ZookingToPropertease.convert_reservation(r, email) for r in zooking_reservations
        ]
        return converted_reservations

    def import_new_or_newly_canceled_reservations(self, user):
        email = user.get("email")
        url = f"{self.url}reservations/upcoming?email={email}"
        LOGGER.info("Importing Zooking NEW or NEWLY CANCELLED reservations for user '%s'", email)
        LOGGER.info("GET request call in Zooking API at '%s'...", url)
        zooking_reservations = requests.get(url=url).json()
        converted_reservations = [
            ZookingToPropertease.convert_reservation(r, email, reservation)
            for r in zooking_reservations
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
            LOGGER.info("Confirming Zooking reservation with: internal_id - '%s'; external_id '%s'", reservation_internal_id, _id)
            url = self.url + f"reservations/{_id}"
            LOGGER.info("PUT request call in Zooking API to confirm reservation at '%s'...", url)
            response = requests.put(url=url, json={"reservation_status": "confirmed"})
            if response.status_code == 200:
                crud.update_reservation(self.service_schema, reservation_internal_id,
                                        response.json()["reservation_status"])
            else:
                LOGGER.error("Error confirming reservation. Response: %s", response.content)
        else:
            LOGGER.info("Creating already confirmed reservation as an event. Reservation_internal_id: '%s'", reservation_internal_id)
            self.create_management_event(property_internal_id, reservation_internal_id, begin_datetime, end_datetime)

    def cancel_overlapping_reservation(self, reservation_internal_id: int):
        _id = crud.get_reservation_external_id(self.service_schema, reservation_internal_id)
        if _id is not None:
            # if it's receiving this message, reservation was already made in this service
            LOGGER.info("Cancelling ClickAndGo OVERLAPPING reservation with: internal_id - '%s'; external_id '%s'", reservation_internal_id, _id)
            url = self.url + f"reservations/{_id}"
            LOGGER.info("PUT request call in ClickAndGo API at '%s'...", url)
            response = requests.put(url=url, json={"reservation_status": "canceled"})
            if response.status_code == 200:
                crud.update_reservation(self.service_schema, reservation_internal_id,
                                        response.json()["reservation_status"])
            else:
                LOGGER.error("Error cancelling reservation with internal_id '%s' and external_id '%s'", reservation_internal_id, _id)
        else:
            LOGGER.error("Reservation with internal_id '%s', requested to cancel doesn't exist", reservation_internal_id)

    def cancel_reservation(self, reservation_internal_id: int, property_internal_id: int):
        _id = crud.get_reservation_external_id(self.service_schema, reservation_internal_id)
        if _id is not None:
            # if reservation made on this service
            LOGGER.info("Cancelling ClickAndGo reservation with: internal_id - '%s'; external_id '%s'", reservation_internal_id, _id)
            url = self.url + f"reservations/{_id}"
            LOGGER.info("PUT request call in ClickAndGo API at '%s'...", url)
            response = requests.put(url=url, json={"reservation_status": "canceled"})
            if response.status_code == 200:
                crud.update_reservation(self.service_schema, reservation_internal_id,
                                        response.json()["reservation_status"])
            else:
                LOGGER.error("Error cancelling reservation. Response: '%s'", response.content)
        else:
            LOGGER.info("Deleting ClickAndGo management event in property '%s', corresponding to reservation with internal_id '%s'", property_internal_id, reservation_internal_id)
            self.delete_management_event(property_internal_id, reservation_internal_id)

            
    def import_new_properties(self, user):
        email = user.get("email")
        LOGGER.info("Importing Zooking NEW properties for user '%s'", email)
        url = f"{self.url}properties?email={email}"
        LOGGER.info("GET request call in Zooking API at '%s'...", url)
        response = requests.get(url=url)
        if response.status_code == 200:
            zooking_properties = response.json()
            # import properties that don't exist -> not mapped in our database
            converted_properties = [
                ZookingToPropertease.convert_property(prop)
                for prop in zooking_properties
                if (crud.get_property_internal_id(self.service_schema, prop.get("id")) is None)
            ]
            return converted_properties
        LOGGER.error("Importing new properties failed with status code %s. Response: %s", response.status_code, response.content)
        return []
