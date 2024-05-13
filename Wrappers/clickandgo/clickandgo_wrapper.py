import requests
import logging

from datetime import datetime
from .converters.clickandgo_to_propertease import ClickandgoToPropertease
from .converters.propertease_to_clickandgo import ProperteaseToClickandgo
from ..base_wrapper.wrapper import BaseWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_CLICKANDGO_ROUTING_KEY, WRAPPER_BROADCAST_ROUTING_KEY,
)
from ..models import Service, ReservationStatus
from ..crud import get_management_event, get_property_external_id, get_property_internal_id, set_property_internal_id, \
    get_reservation_external_id, get_reservation_by_external_id, create_management_event

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class CNGWrapper(BaseWrapper):
    def __init__(self, queue: str) -> None:
        super().__init__(
            url="http://host.docker.internal:8002/",
            queue=queue,
            service_schema=Service.CLICKANDGO,
        )
        cng_queue = channel.queue_declare(queue=self.queue, durable=True)
        channel.queue_bind(
            queue=cng_queue.method.queue,
            exchange=EXCHANGE_NAME,
            routing_key=WRAPPER_CLICKANDGO_ROUTING_KEY,
        )
        channel.queue_bind(
            queue=cng_queue.method.queue,
            exchange=EXCHANGE_NAME,
            routing_key=WRAPPER_BROADCAST_ROUTING_KEY,
        )

    def create_property(self, property):
        url = self.url + "properties"
        LOGGER.info("Creating property in ClickAndGo external API: %s", property)
        requests.post(url=url, json=property)

    def update_property(self, prop_internal_id: int, prop_update_parameters: dict):
        external_id = get_property_external_id(self.service_schema, prop_internal_id)
        url = self.url + f"properties/{external_id}"
        LOGGER.info("Updating property in ClickAndGo external API. Internal_id - '%s'; External_id - '%s'. Update parameters: %s", prop_internal_id, external_id, prop_update_parameters)
        requests.put(url=url, json=ProperteaseToClickandgo.convert_property(prop_update_parameters))

    def delete_property(self, property):
        _id = property.get("id")
        LOGGER.info("Deleting property in ClickAndGo external API: %s", property)
        url = self.url + f"properties/{_id}"
        requests.delete(url=url)

    def create_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: str,
                                end_datetime: str):
        LOGGER.info("Creating Management Event in ClickAndGo external API for property_internal_id '%s': Event_internal_id - '%s'; Begin_datetime - '%s'; End_datetime - '%s'", 
                    property_internal_id, event_internal_id, begin_datetime, end_datetime)
        property_external_id = get_property_external_id(self.service_schema, property_internal_id)
        if property_external_id is None:
            LOGGER.error("Trying to create a management event for a non-existing property with internal_id '%s'", property_internal_id)
            return
        event_post_body = {
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        }
        url = self.url + f"properties/{property_external_id}/events"
        LOGGER.info("POST request call (create management event for property with external_id '%s') in ClickAndGo API at '%s'...", property_external_id, url)
        res = requests.post(url, json=event_post_body)
        if res.status_code == 201:
            property_after_creating_event = res.json()
            returned_closed_time_frames = property_after_creating_event["closed_time_frames"]
            for management_event_id, management_event in returned_closed_time_frames.items():
                if (management_event["begin_datetime"] == begin_datetime and
                        management_event["end_datetime"] == end_datetime):
                    # management_event_id is the external id
                    create_management_event(self.service_schema, event_internal_id, management_event_id)
                    LOGGER.info("Successfully created management event with internal_id '%s'", event_internal_id)
                    return
        LOGGER.error("Failed to create management event with internal_id '%s'", event_internal_id)

    def update_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: str,
                                end_datetime: str):
        LOGGER.info("Updating Management Event in ClickAndGo external API for property_internal_id '%s': Event_internal_id - '%s'; Begin_datetime - '%s'; End_datetime - '%s'", 
                    property_internal_id, event_internal_id, begin_datetime, end_datetime)
        property_external_id = get_property_external_id(self.service_schema, property_internal_id)
        if property_external_id is None:
            LOGGER.error("Trying to update a management event for a non-existing property with internal_id '%s'", property_internal_id)
            return

        management_event_external = get_management_event(self.service_schema, event_internal_id)

        if management_event_external is None:
            LOGGER.error("Trying to update a management event that does NOT exist - event_internal_id '%s'", event_internal_id)
            return

        update_parameters = {
            "id": management_event_external.external_id,
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        }
        url = self.url + f"properties/{property_external_id}/events/{management_event_external.external_id}"
        LOGGER.info("PUT request call (to update management event for property_external_id '%s') in ClickAndGo API at '%s'...", property_external_id, url)
        res = requests.put(url=url, json=update_parameters)
        if res.status_code == 200:
            LOGGER.info("Successfully updated management event with internal_id '%s'", event_internal_id)
            return
        LOGGER.error("Failed to update management event with internal_id '%s'", event_internal_id)

    def delete_management_event(self, property_internal_id: int, event_internal_id: int):
        LOGGER.info("Deleting Management Event in ClickAndGo external API for property_internal_id '%s': Event_internal_id - '%s'", 
                    property_internal_id, event_internal_id)
        property_external_id = get_property_external_id(self.service_schema, property_internal_id)
        if property_external_id is None:
            LOGGER.error("Trying to delete a management event for a non-existing property with internal_id '%s'", property_internal_id)
            return

        management_event_external = get_management_event(self.service_schema, event_internal_id)

        if management_event_external is None:
            LOGGER.error("External counterpart of management event with internal_id '%s' not found.", event_internal_id)
            return

        url = self.url + f"properties/{property_external_id}/events/{management_event_external.external_id}"
        LOGGER.info("PUT request call (to delete management event for property_external_id '%s') in ClickAndGo API at '%s'... Deleting event_external_id '%s'", 
                    property_external_id, url, management_event_external.external_id)

        res = requests.delete(url=url)
        if res.status_code == 204:  # no content
            LOGGER.info("Successfully deleted management event with internal_id '%s'", event_internal_id)

    def import_properties(self, user):
        email = user.get("email")
        url = self.url + "properties?email=" + email
        LOGGER.info("Importing ClickAndGo properties for user '%s'", email)
        LOGGER.info("GET request call in ClickAndGo API at '%s'", url)
        clickandgo_properties = requests.get(url=url).json()
        converted_properties = [
            ClickandgoToPropertease.convert_property(p) for p in clickandgo_properties
        ]
        return converted_properties

    def import_reservations(self, user):
        email = user.get("email")
        url = self.url + "reservations?email=" + email
        LOGGER.info("Importing ClickAndGo reservations for user '%s'", email)
        LOGGER.info("GET request call in ClickAndGo API at '%s'..", url)
        clickandgo_reservations = requests.get(url=url).json()
        converted_properties = [
            ClickandgoToPropertease.convert_reservation(r, email) for r in clickandgo_reservations
        ]
        return converted_properties

    def import_new_or_newly_canceled_reservations(self, user):
        email = user.get("email")
        url = f"{self.url}reservations/upcoming?email={email}"
        LOGGER.info("Importing ClickAndGo NEW or NEWLY CANCELLED reservations for user '%s'", email)
        LOGGER.info("GET request call in ClickAndGo API at '%s'...", url)
        clickandgo_reservations = requests.get(url=url).json()
        converted_reservations = [
            ClickandgoToPropertease.convert_reservation(r, email, reservation)
            for r in clickandgo_reservations
            if get_property_internal_id(self.service_schema, r["property_id"]) is not None and
               ((reservation := get_reservation_by_external_id(self.service_schema, r["id"])) is None or
                (r[
                     "reservation_status"] == "canceled" and reservation.reservation_status != ReservationStatus.CANCELED))
        ]
        return converted_reservations

    def confirm_reservation(self, reservation_internal_id):
        _id = get_reservation_external_id(self.service_schema, reservation_internal_id)
        LOGGER.info("Confirming ClickAndGo reservation with: internal_id - '%s'; external_id '%s'", reservation_internal_id, _id)
        url = self.url + f"reservations/{_id}"
        LOGGER.info("PUT request call in ClickAndGo API to confirm reservation at '%s'...", url)
        requests.put(url=url, json={"reservation_status": "confirmed"})

    def delete_reservation(self, reservation_internal_id):
        _id = get_reservation_external_id(self.service_schema, reservation_internal_id)
        LOGGER.info("Deleting ClickAndGo reservation with: internal_id - '%s'; external_id '%s'", reservation_internal_id, _id)
        url = self.url + f"reservations/{_id}"
        LOGGER.info("DELETE request call in ClickAndGo API at '%s'...", url)
        print("Deleting reservation...", reservation_internal_id)
        requests.delete(url=url)

    def import_new_properties(self, user):
        email = user.get("email")
        LOGGER.info("Importing ClickAndGo NEW properties for user '%s'", email)
        url = f"{self.url}properties?email={email}"
        LOGGER.info("GET request call in ClickAndGo API at '%s'...", url)
        response = requests.get(url=url)
        if response.status_code == 200:
            clickandgo_properties = response.json()
            # import properties that don't exist -> not mapped in our database
            converted_properties = [
                ClickandgoToPropertease.convert_property(prop)
                for prop in clickandgo_properties
                if (get_property_internal_id(self.service_schema, prop.get("id")) is None)
            ]
            return converted_properties
        return []