import requests

from .propertease_to_zooking import ProperteaseToZooking
from .zooking_to_propertease import ZookingToPropertease
from ..base_wrapper.api_wrapper import BaseAPIWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_ZOOKING_ROUTING_KEY, WRAPPER_BROADCAST_ROUTING_KEY,
)
from ..models import SessionLocal, IdMapperZooking, get_property_mapped_id, Service, get_property_external_id


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
        # TODO does not match signature of base method (although it runs anyway)
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



"""
Propertease Property Schema Example:

{
    "id": "661a7e5ab7bd0512178cf014",
    "user_id": 1,
    "title": "Coolest house ever",
    "address": "Braga (obvio que nao)",
    "description": "Dont enter",
    "number_guests": 20,
    "square_meters": 4000,
    "bedrooms": {
        "bedroom_1": {
            "beds": [
                {
                    "number_beds": 1,
                    "type": "single"
                }
            ]
        }
    },
    "bathrooms": {
        "bathroom_1": {
            "fixtures": [
                "bathtub",
                "shower"
            ]
        }
    },
    "amenities": [
        "free_wifi",
        "pool",
        "kitchen"
    ],
    "house_rules": {
        "check_in": {
            "begin_time": "10:59",
            "end_time": "20:40"
        },
        "check_out": {
            "begin_time": "10:59",
            "end_time": "20:40"
        },
        "smoking": false,
        "parties": true,
        "rest_time": {
            "begin_time": "23:00",
            "end_time": "06:00"
        },
        "allow_pets": true
    },
    "additional_info": "So pessoas fixes",
    "cancellation_policy": "😀",
    "contacts": [
        {
            "name": "Alvaro Barbosa",
            "phone_number": "+351969314716"
        }
    ]
}


Zooking Property Schema example:

{
    "user_email": "joao.p.dourado1@gmail.com",
    "name": "Test home",
    "address": "Rua 1234",
    "curr_price": 140.0,
    "description": "Tem muito sol",
    "number_of_guests": 4,
    "square_meters": 2000,
    "bedrooms": [
        {
            "number_beds": 2,
            "bed_type": "single_bed"
        },
        {
            "number_beds": 1,
            "bed_type": "queen_bed"
        }
    ],
    "bathrooms": [
        {
            "name": "bathroom_groundfloor",
            "bathroom_fixtures": [
                "toilet"
            ]
        },
        {
            "name": "bathroom_topfloor",
            "bathroom_fixtures": [
                "toilet",
                "shower"
            ]
        }
    ],
    "amenities": [
        "AC",
        "wifi",
        "open_parking"
    ],
    "additional_info": "Se cá aparecerem, pagam"
}

"""
