from datetime import datetime

import requests

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


class ZookingWrapper(BaseWrapper):
    def __init__(self, queue: str) -> None:
        super().__init__(
            url="http://localhost:8000/",
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
        print("Creating property...")
        requests.post(url=url, json=property)

    def update_property(self, prop_internal_id: int, prop_update_parameters: dict):
        external_id = crud.get_property_external_id(self.service_schema, prop_internal_id)
        url = self.url + f"properties/{external_id}"
        print("Updating property...")
        print("internal_id", prop_internal_id, "external_id", external_id)
        print("update_parameters", prop_update_parameters)
        response = requests.put(url=url, json=ProperteaseToZooking.convert_property(prop_update_parameters))
        return response

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

        url = self.url + f"properties/{external_id}"
        update_parameters = {"closed_time_frames": [{
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        }]}
        response = requests.put(url=url, json=ProperteaseToZooking.convert_property(update_parameters))
        # TODO implement check against different status codes later
        if response.status_code == 200:
            print("Success creating management event")
            updated_property = response.json()
            returned_closed_time_frames = updated_property["closed_time_frames"]
            for management_event_id, management_event in returned_closed_time_frames.items():
                if (management_event["begin_datetime"] == begin_datetime and
                        management_event["end_datetime"] == end_datetime):
                    # management_event_id is the external id
                    crud.create_management_event(self.service_schema, event_internal_id, management_event_id)
                    break
        else:
            print("Failed creating management event", response.json())

    def update_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: str,
                                end_datetime: str):

        external_id = crud.get_property_external_id(self.service_schema, property_internal_id)
        if external_id is None:
            print(f"Property with internal_id {property_internal_id} not found in IdMapper database.")
            return

        url = self.url + f"properties/{external_id}"
        update_parameters = {"closed_time_frames": [{
            "id": crud.get_management_event(self.service_schema, event_internal_id).external_id,
            "begin_datetime": begin_datetime,
            "end_datetime": end_datetime
        }]}
        response = requests.put(url=url, json=ProperteaseToZooking.convert_property(update_parameters))
        if response.status_code == 200:
            print("Success updating management event")
        else:
            print("Failed updating management event", response.json())
        # TODO implement check against different status codes later
        # don't need to update anything on the mappers

    def delete_management_event(self, property_internal_id: int, event_internal_id: int):
        external_id = crud.get_property_external_id(self.service_schema, property_internal_id)
        if external_id is None:
            print(f"Property with internal_id {property_internal_id} not found in IdMapper database.")
            return

        url = self.url + f"properties/{external_id}"
        update_parameters = {"closed_time_frames": [{
            "id": crud.get_management_event(self.service_schema, event_internal_id).external_id,
        }]}
        response = requests.put(url=url, json=ProperteaseToZooking.convert_property(update_parameters))
        # TODO implement check against different status codes later
        if response.status_code == 200:
            print("Success deleting management event")
            crud.delete_management_event(self.service_schema, event_internal_id)
        else:
            print("Failed deleting management event", response.json())

    def import_properties(self, user):
        url = self.url + "properties?email=" + user.get("email")
        print("Importing properties...")
        zooking_properties = requests.get(url=url).json()
        converted_properties = [
            ZookingToPropertease.convert_property(p) for p in zooking_properties
        ]
        return converted_properties

    def import_reservations(self, user):
        email = user.get("email")
        url = self.url + "reservations?email=" + email
        print("Importing reservations...")
        zooking_reservations = requests.get(url=url).json()
        converted_reservations = [
            ZookingToPropertease.convert_reservation(r, email) for r in zooking_reservations
        ]
        return converted_reservations

    def import_new_or_newly_canceled_reservations(self, user):
        email = user.get("email")
        url = f"{self.url}reservations/upcoming?email={email}"
        print("Importing new reservations...")
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
            url = self.url + f"reservations/{_id}"
            print("Confirming existing reservation...", reservation_internal_id)
            response = requests.put(url=url, json={"reservation_status": "confirmed"})
            if response.status_code == 200:
                crud.update_reservation(self.service_schema, reservation_internal_id,
                                        response.json()["reservation_status"])
            else:
                print("Error confirming reservation")
        else:
            print("Creating already confirmed reservation as an event...", reservation_internal_id)
            self.create_management_event(property_internal_id, reservation_internal_id, begin_datetime, end_datetime)

    def cancel_reservation(self, reservation_internal_id):
        _id = crud.get_reservation_external_id(self.service_schema, reservation_internal_id)
        url = self.url + f"reservations/{_id}"
        print("Cancelling existing reservation...", reservation_internal_id)
        response = requests.put(url=url, json={"reservation_status": "canceled"})
        if response.status_code == 200:
            crud.update_reservation(self.service_schema, reservation_internal_id, response.json()["reservation_status"])
        else:
            print("Error cancelling reservation")
