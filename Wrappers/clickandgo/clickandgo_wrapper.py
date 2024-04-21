import requests

from .converters.clickandgo_to_propertease import ClickandgoToPropertease
from .converters.propertease_to_clickandgo import ProperteaseToClickandgo
from ..base_wrapper.api_wrapper import BaseAPIWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_CLICKANDGO_ROUTING_KEY, WRAPPER_BROADCAST_ROUTING_KEY,
)
from ..models import set_and_get_property_internal_id, Service, get_property_external_id


class CNGAPIWrapper(BaseAPIWrapper):
    def __init__(self) -> None:
        super().__init__()
        self.url = "http://localhost:8002/"
        self.queue = "clickandgo_queue"
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
        print("Creating property...")
        requests.post(url=url, json=property)

    def update_property(self, prop_internal_id: int, prop_update_parameters: dict):
        # TODO does not match signature of base method (although it runs anyway)
        external_id = get_property_external_id(Service.CLICKANDGO, prop_internal_id)
        url = self.url + f"properties/{external_id}"
        print("Updating property...")
        print("internal_id", prop_internal_id, "external_id", external_id)
        print("update_parameters", prop_update_parameters)
        requests.put(url=url, json=ProperteaseToClickandgo.convert_property(prop_update_parameters))

    def delete_property(self, property):
        _id = property.get("id")
        print("Deleting property...")
        url = self.url + f"properties/{_id}"
        requests.delete(url=url)

    def import_properties(self, user):
        url = self.url + "properties?email=" + user.get("email")
        print("Importing properties...")
        clickandgo_properties = requests.get(url=url).json()
        converted_properties = [
            ClickandgoToPropertease.convert_property(p) for p in clickandgo_properties
        ]
        return converted_properties

