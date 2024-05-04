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
from ..crud import get_property_external_id, get_property_internal_id, set_property_internal_id, \
    get_reservation_external_id, get_reservation_by_external_id


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
        external_id = get_property_external_id(self.service_schema, prop_internal_id)
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
            if get_property_internal_id(self.service_schema, r["property_id"]) is not None and
               ((reservation := get_reservation_by_external_id(self.service_schema, r["id"])) is None or
               (r["reservation_status"] == "canceled" and reservation.reservation_status != ReservationStatus.CANCELED))
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
