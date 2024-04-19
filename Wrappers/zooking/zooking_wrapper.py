import requests
from ..base_wrapper.api_wrapper import BaseAPIWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_ZOOKING_ROUTING_KEY,
)
from ..models import SessionLocal, IdMapperZooking, get_property_mapped_id, Service


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

    def create_property(self, property):
        url = self.url + "properties"
        print("Creating property...")
        requests.post(url=url, json=property)

    def update_property(self, property):
        _id = property.get("id")
        url = self.url + f"properties/{_id}"
        print("Updating property...")
        requests.put(url=url, json=property)

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
            self.property_from_zooking_to_propertease(p) for p in zooking_properties
        ]
        return converted_properties

    """
        Converts property from the Zooking API schema to the Propertease schema.
    """

    def property_from_zooking_to_propertease(self, zooking_property):
        propertease_property = {}
        propertease_property["_id"] = get_property_mapped_id(Service.ZOOKING, zooking_property.get("id"))
        propertease_property["user_email"] = zooking_property.get("user_email")
        propertease_property["title"] = zooking_property.get("name")
        propertease_property["address"] = zooking_property.get("address")
        propertease_property["description"] = zooking_property.get("description")
        propertease_property["price"] = zooking_property.get("curr_price")
        propertease_property["number_guests"] = zooking_property.get("number_of_guests")
        propertease_property["square_meters"] = zooking_property.get("square_meters")
        propertease_property["bedrooms"] = self.zooking_to_propertease_bedroom(
            zooking_property.get("bedrooms")
        )
        propertease_property["bathrooms"] = self.zooking_to_propertease_bathroom(
            zooking_property.get("bathrooms")
        )
        propertease_property["amenities"] = self.zooking_to_propertease_amenities(
            zooking_property.get("amenities")
        )
        # not supported in zooking
        propertease_property["house_rules"] = (
            self.empty_house_rules()
        )  
        propertease_property["additional_info"] = zooking_property.get(
            "additional_info"
        )
        propertease_property["cancellation_policy"] = ""  # not supported in zooking
        propertease_property["contacts"] = []  # not supported in Zooking

        return propertease_property

    def zooking_to_propertease_bedroom(self, zooking_bedrooms):
        bedroom_type_map = {
            "single_bed": "single",
            "king_bed": "king",
            "queen_bed": "queen",
        }
        bedrooms_converted = {}
        for i in range(0, len(zooking_bedrooms)):
            bedroom_name = "bedroom_" + str(i)
            bedrooms_converted[bedroom_name] = {
                "beds": [
                    {
                        "number_beds": zooking_bedrooms[i].get("number_beds"),
                        "type": bedroom_type_map.get(
                            zooking_bedrooms[i].get("bed_type")
                        ),
                    }
                ]
            }
        return bedrooms_converted

    def zooking_to_propertease_bathroom(self, zooking_bathrooms):
        fixtures_map = {"tub": "bathtub", "shower": "shower", "toilet": "toilet"}
        bathrooms_converted = {}
        for bathroom in zooking_bathrooms:
            bathrooms_converted[bathroom.get("name")] = {
                "fixtures": [
                    fixtures_map[zook_fixture]
                    for zook_fixture in bathroom.get("bathroom_fixtures")
                ]
            }
        return bathrooms_converted

    def zooking_to_propertease_amenities(self, zooking_amenities):
        amenities_map = {
            "AC": "air_conditioner",
            "wifi": "free_wifi",
            "open_parking": "parking_space",
        }
        # there might be amenities in zooking that don't exist in propertease,
        return [
            amenities_map[zook_amen]
            for zook_amen in zooking_amenities
            if zook_amen in amenities_map.keys()
        ]

    def empty_house_rules(self):
        return {
            "check_in": {
                "begin_time": "00:00",
                "end_time": "00:00",
            },
            "check_out": {
                "begin_time": "00:00",
                "end_time": "00:00",
            },
            "smoking": False,
            "parties": False,
            "rest_time": {
                "begin_time": "00:00",
                "end_time": "00:00",
            },
            "allow_pets": False,
        }


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
