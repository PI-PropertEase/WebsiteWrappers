import requests
from ..base_wrapper.api_wrapper import BaseAPIWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_EARTHSTAYIN_ROUTING_KEY,
)
from ..models import set_and_get_property_internal_id, Service


class EarthStayinAPIWrapper(BaseAPIWrapper):
    def __init__(self) -> None:
        super().__init__()
        self.url = "http://localhost:8001/"
        self.queue = "earthstayin_queue"
        earthstayin_queue = channel.queue_declare(queue=self.queue, durable=True)
        channel.queue_bind(
            queue=earthstayin_queue.method.queue,
            exchange=EXCHANGE_NAME,
            routing_key=WRAPPER_EARTHSTAYIN_ROUTING_KEY,
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
        earthstayin_properties = requests.get(url=url).json()
        converted_properties = [
            self.property_from_earthstayin_to_propertease(p) for p in earthstayin_properties
        ]
        return converted_properties

    """
        Converts property from the EarthStayin API schema to the Propertease schema.
    """

    def property_from_earthstayin_to_propertease(self, earthstayin_property):
        propertease_property = {}
        propertease_property["_id"] = set_and_get_property_internal_id(Service.EARTHSTAYIN, earthstayin_property.get("id"))
        propertease_property["user_email"] = earthstayin_property.get("user_email")
        propertease_property["title"] = earthstayin_property.get("name")
        propertease_property["address"] = earthstayin_property.get("address")
        propertease_property["description"] = earthstayin_property.get("description")
        propertease_property["price"] = earthstayin_property.get("curr_price")
        propertease_property["number_guests"] = earthstayin_property.get("number_of_guests")
        propertease_property["square_meters"] = earthstayin_property.get("square_meters")
        propertease_property["bedrooms"] = self.earthstayin_to_propertease_bedroom(
            earthstayin_property.get("bedrooms")
        )
        propertease_property["bathrooms"] = self.earthstayin_to_propertease_bathroom(
            earthstayin_property.get("bathrooms")
        )
        propertease_property["amenities"] = self.earthstayin_to_propertease_amenities(
            earthstayin_property.get("amenities")
        )
        propertease_property["house_rules"] = self.earthstayin_to_propertease_house_rules(
            earthstayin_property.get("house_rules")
        )
        propertease_property["additional_info"] = earthstayin_property.get(
            "additional_info"
        ) + ". This property has the following accessibilities: " + ", ".join(
            earthstayin_property.get("accessibilities")
        )
        propertease_property["cancellation_policy"] = ""  # not supported in earthstayin
        propertease_property["contacts"] = []  # not supported in earthstayin

        return propertease_property

    def earthstayin_to_propertease_bedroom(self, earthstayin_bedrooms):
        bedroom_type_map = {
            "single_bed": "single",
            "king_bed": "king",
            "queen_bed": "queen",
            "twin_bed": "single",
        }

        bedrooms_converted = {}
        for name, beds in earthstayin_bedrooms.items():
            bedrooms_converted[name] = {
                "beds": [
                    {
                        "number_beds": bed.get("number_beds"),
                        "type": bedroom_type_map.get(
                            bed.get("bed_type")
                        ),
                    }
                    for bed in beds if bed.get("bed_type") in bedroom_type_map
                ]
            }
        return bedrooms_converted

    def earthstayin_to_propertease_bathroom(self, earthstayin_bathrooms):
        fixtures_map = {"tub": "bathtub", "shower": "shower", "toilet": "toilet", "bidet": "bidet"}
        bathrooms_converted = {}
        for i in range(0, len(earthstayin_bathrooms)):
            bathrooms_converted["bathroom_" + str(i)] = {
                "fixtures": [
                    fixtures_map[earthstayin_fixture]
                    for earthstayin_fixture in earthstayin_bathrooms[i].get("bathroom_fixtures")
                ]
            }
        return bathrooms_converted

    def earthstayin_to_propertease_amenities(self, earthstayin_amenities):
        amenities_map = {
            "AC": "air_conditioner",
            "wifi": "free_wifi",
            "car_parking": "parking_space",
        }
        # there might be amenities in earthstayin that don't exist in propertease,
        return [
            amenities_map[earthstayin_amen]
            for earthstayin_amen in earthstayin_amenities
            if earthstayin_amen in amenities_map.keys()
        ]

    def earthstayin_to_propertease_house_rules(self, earthstayin_house_rules):
        check_in_times = earthstayin_house_rules.get("checkin_time").split("-")
        check_out_times = earthstayin_house_rules.get("checkout_time").split("-")
        smoking_allowed = earthstayin_house_rules.get("smoking_allowed")
        rest_time = earthstayin_house_rules.get("rest_time").split("-")
        pets_allowed = earthstayin_house_rules.get("pets_allowed")
        house_rules = {
            "check_in": {
                "begin_time": check_in_times[0],
                "end_time": check_in_times[1],
            },
            "check_out": {
                "begin_time": check_out_times[0],
                "end_time": check_out_times[1],
            },
            "smoking": smoking_allowed,
            "parties": False,
            "rest_time": {
                "begin_time": rest_time[0],
                "end_time": "08:00",
            },
            "allow_pets": pets_allowed,
        }
        return house_rules


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


EarthStayin Property Schema example:

{
    "user_email": "alicez@gmail.com",
    "name": "Poente Azul 2",
    "address": "Rua 5678   2",
    "curr_price": 25.5,
    "description": "A segunda casa mais azul do bairro, desde 1999",
    "number_of_guests": 5,
    "square_meters": 2500,
    "bedrooms": [
        {
            "number_beds": 1,
            "bed_type": "king_bed"
        }
    ],
    "bathrooms": [
        {
            "name": "bathroom_groundfloor",
            "bathroom_fixtures": [
                "toilet",
                "tub"
            ]
        }
    ],
    "amenities": [
        "free_wifi",
        "AC"
    ],
    "accessibilities": ["ramp"],
    "additional_info": "Um rebuçado por cada hóspede."
    "house_rules": {
        "checkin_time": "14:00-23:59",
        "checkout_time": "00:00-10:30",
        "smoking_allowed": true,
        "rest_time": "22:00",
        "pets_allowed": false
    }
}

"""