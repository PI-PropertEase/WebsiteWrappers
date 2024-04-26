import requests

from Wrappers.zooking.converters.propertease_to_zooking import ProperteaseToZooking
from Wrappers.zooking.converters.zooking_to_propertease import ZookingToPropertease
from ..base_wrapper.api_wrapper import BaseAPIWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_ZOOKING_ROUTING_KEY, WRAPPER_BROADCAST_ROUTING_KEY,
)
from ..models import Service, get_property_external_id, get_reservation_external_id, get_reservation_internal_id


class ZookingAPIWrapper(BaseAPIWrapper):
    def __init__(self) -> None:
        super().__init__()
        self.url = "http://localhost:8000/"
        self.queue = "zooking_queue"
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
        external_id = get_property_external_id(Service.ZOOKING, prop_internal_id)
        url = self.url + f"properties/{external_id}"
        print("Updating property...")
        print("internal_id", prop_internal_id, "external_id", external_id)
        print("update_parameters", prop_update_parameters)
        requests.put(url=url, json=ProperteaseToZooking.convert_property(prop_update_parameters))

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

    def import_new_pending_or_canceled_reservations(self, user):
        email = user.get("email")
        url = f"{self.url}reservations/upcoming?email={email}"
        print("Importing new pending reservations...")
        zooking_reservations = requests.get(url=url).json()
        converted_reservations = [
            ZookingToPropertease.convert_reservation(r, email, internal_id)
            for r in zooking_reservations
            if (internal_id := get_reservation_internal_id(Service.ZOOKING, r["id"])) is None or r["reservation_status"] == "canceled"
        ]
        return converted_reservations

    def confirm_reservation(self, reservation_internal_id):
        _id = get_reservation_external_id(Service.ZOOKING, reservation_internal_id)
        url = self.url + f"reservations/{_id}"
        print("Confirming reservation...", reservation_internal_id)
        requests.put(url=url, json={"reservation_status": "confirmed"})

    def delete_reservation(self, reservation_internal_id):
        _id = get_reservation_external_id(Service.ZOOKING, reservation_internal_id)
        url = self.url + f"reservations/{_id}"
        print("Deleting reservation...", reservation_internal_id)
        requests.delete(url=url)


