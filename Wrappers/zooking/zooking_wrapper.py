import requests

from Wrappers.zooking.converters.propertease_to_zooking import ProperteaseToZooking
from Wrappers.zooking.converters.zooking_to_propertease import ZookingToPropertease
from ..base_wrapper.wrapper import BaseWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_ZOOKING_ROUTING_KEY, WRAPPER_BROADCAST_ROUTING_KEY,
)
from ..models import Service, get_property_external_id, get_reservation_external_id, \
    get_reservation_by_external_id, ReservationStatus, get_property_internal_id, create_management_event


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
        external_id = get_property_external_id(self.service_schema, prop_internal_id)
        url = self.url + f"properties/{external_id}"
        print("Updating property...")
        print("internal_id", prop_internal_id, "external_id", external_id)
        print("update_parameters", prop_update_parameters)
        response = requests.put(url=url, json=ProperteaseToZooking.convert_property(prop_update_parameters))
        print("\n\ncontent", response.content)
        if response.status_code == 200:
            updated_property = response.json()
            to_insert_closed_time_frames = prop_update_parameters.get("closed_time_frames")
            if to_insert_closed_time_frames is None:
                return
            inserted_begin_datetime = to_insert_closed_time_frames[0].get("begin_datetime")
            inserted_end_datetime = to_insert_closed_time_frames[0].get("end_datetime")
            closed_time_frames = updated_property["closed_time_frames"]
            for management_event_id, management_event in closed_time_frames.items():
                print(management_event_id, management_event)
                print(type(management_event["begin_datetime"]), type(inserted_begin_datetime))
                if management_event["begin_datetime"] != inserted_begin_datetime or \
                        management_event["end_datetime"] != inserted_end_datetime:
                    continue
                # external_id of event -> going to be mapped where we call this function
                return management_event_id

    def delete_property(self, property):
        _id = property.get("id")
        print("Deleting property...")
        url = self.url + f"properties/{_id}"
        requests.delete(url=url)

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
            if get_property_internal_id(self.service_schema, r["property_id"]) is not None and
               ((reservation := get_reservation_by_external_id(self.service_schema, r["id"])) is None or
                (r[
                     "reservation_status"] == "canceled" and reservation.reservation_status != ReservationStatus.CANCELED))
        ]
        return converted_reservations

    def confirm_reservation(self, reservation_internal_id):
        _id = get_reservation_external_id(self.service_schema, reservation_internal_id)
        url = self.url + f"reservations/{_id}"
        print("Confirming reservation...", reservation_internal_id)
        requests.put(url=url, json={"reservation_status": "confirmed"})

    def delete_reservation(self, reservation_internal_id):
        _id = get_reservation_external_id(self.service_schema, reservation_internal_id)
        url = self.url + f"reservations/{_id}"
        print("Deleting reservation...", reservation_internal_id)
        requests.delete(url=url)
