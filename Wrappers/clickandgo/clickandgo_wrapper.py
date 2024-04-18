import requests
from ..base_wrapper.api_wrapper import BaseAPIWrapper
from ProjectUtils.MessagingService.queue_definitions import (
    channel,
    EXCHANGE_NAME,
    WRAPPER_CLICKANDGO_ROUTING_KEY,
)
from ..models import SessionLocal, IdMapperZooking, get_property_mapped_id


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
        clickandgo_properties = requests.get(url=url).json()
        converted_properties = [
            self.property_from_clickandgo_to_propertease(p) for p in clickandgo_properties
        ]
        return converted_properties

    """
        Converts property from the ClickAndGo API schema to the Propertease schema.
    """
    def property_from_clickandgo_to_propertease(self, clickandgo_property):
        propertease_property = {}
        propertease_property["_id"] = get_property_mapped_id(
            clickandgo_property.get("id")
        )
        propertease_property["user_email"] = clickandgo_property.get("user_email")
        propertease_property["title"] = clickandgo_property.get("name")
        propertease_property["address"] = clickandgo_property.get("address")
        propertease_property["description"] = clickandgo_property.get("description")
        propertease_property["price"] = clickandgo_property.get("curr_price")
        propertease_property["number_guests"] = clickandgo_property.get("guest_num")
        propertease_property["square_meters"] = clickandgo_property.get("house_area")
        propertease_property["bedrooms"] = self.clickandgo_to_propertease_bedroom(
            clickandgo_property.get("bedrooms")
        )
        propertease_property["bathrooms"] = self.clickandgo_to_propertease_bathroom(
            clickandgo_property.get("bathrooms")
        )
        propertease_property["amenities"] = self.clickandgo_to_propertease_amenities(
            clickandgo_property.get("available_amenities")
        )
        # not supported in CNG
        propertease_property["house_rules"] = self.clickandgo_to_propertease_houserules(
            clickandgo_property.get("house_rules")
        )
        propertease_property["additional_info"] = clickandgo_property.get(
            "additional_info"
        )
        propertease_property["cancellation_policy"] = ""  # not supported in CNG
        propertease_property["contacts"] = self.clickandgo_to_propertease_contacts(
            clickandgo_property.get("house_manager")
        )

        return propertease_property

    def clickandgo_to_propertease_bedroom(self, clickandgo_bedrooms):
        bedroom_type_map = {
            "single": "single",
            "king": "king",
            "queen": "queen",
            "twin": "single",
        }

        bedrooms_converted = {}
        for i in range(0, len(clickandgo_bedrooms)):
            if clickandgo_bedrooms[i].get("bed_type") not in bedroom_type_map:
                continue
            bedroom_name = "bedroom_" + str(i)
            bedrooms_converted[bedroom_name] = {
                "beds": [
                    {
                        "number_beds": clickandgo_bedrooms[i].get("number_beds"),
                        "type": bedroom_type_map.get(
                            clickandgo_bedrooms[i].get("bed_type")
                        ),
                    }
                ]
            }
        return bedrooms_converted

    def clickandgo_to_propertease_bathroom(self, clickandgo_bathrooms):
        fixtures_map = {"tub": "bathtub", "shower": "shower", "toilet": "toilet"}
        bathrooms_converted = {}
        for i in range(0, len(clickandgo_bathrooms)):
            bathroom_name = "bathroom_" + str(i)
            curr_bathroom = clickandgo_bathrooms[i]
            bathrooms_converted[bathroom_name] = {
                "fixtures": [
                    fixtures_map[cng_fixture]
                    for cng_fixture in curr_bathroom.get("bathroom_fixtures") if cng_fixture in fixtures_map
                ]
            }
        return bathrooms_converted

    def clickandgo_to_propertease_amenities(self, clickandgo_amenities):
        amenities_map = {
            "AC": "air_conditioner",
            "wifi": "free_wifi",
            "open_parking": "parking_space",
        }
        # there might be amenities in clickandgo that don't exist in propertease
        return [
            amenities_map[cng_amen]
            for cng_amen in clickandgo_amenities
            if cng_amen in amenities_map.keys()
        ]

    def clickandgo_to_propertease_houserules(self, clickandgo_houserules):
        check_in_parts = clickandgo_houserules.get("check_in").split("-")
        check_out_parts = clickandgo_houserules.get("check_out").split("-")
        rest_time_parts = clickandgo_houserules.get("rest_time").split("-")
        return {
            "check_in": {
                "begin_time": check_in_parts[0],
                "end_time": check_in_parts[1],
            },
            "check_out": {
                "begin_time": check_out_parts[0],
                "end_time": check_out_parts[1],
            },
            "smoking": clickandgo_houserules.get("smoking_allowed"),
            "parties": clickandgo_houserules.get("parties_allowed"),
            "rest_time": {
                "begin_time": rest_time_parts[0],
                "end_time": rest_time_parts[1],
            },
            "allow_pets": clickandgo_houserules.get("pets_allowed"),
        }

    def clickandgo_to_propertease_contacts(self, clickandgo_housemanager):
        return [
            {
                "name": clickandgo_housemanager.get("name"),
                "phone_number": clickandgo_housemanager.get("phone_number"),
            }
        ]


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


ClickAndGo Property Schema example:

{
    "id": 1,
    "user_email": "alicez@gmail.com",
    "name": "MUITA ahdashashdasjasjsajsajas!!!!",
    "address": "Rua kakakalalalazl457346235213512414",
    "curr_price": 555555.0,
    "description": "CASA ASSOMBRADA !! SCARYRYRYRY",
    "guest_num": 55,
    "house_area": 2005,
    "bedrooms": [
        {
            "number_beds": 25,
            "bed_type": "king"
        }
    ],
    "bathrooms": [
        {
            "bathroom_fixtures": [
                "toilet",
                "tub",
                "shower"
            ]
        }
    ],
    "available_amenities": [
        "AC",
        "patio",
        "wifi_free",
        "parking"
    ],
    "house_rules": {
        "check_in": "16:00-23:59",
        "check_out": "00:00-10:00",
        "smoking_allowed": false,
        "parties_allowed": true,
        "rest_time": "22:59-08:01",
        "pets_allowed": true
    },
    "additional_info": "Somos os mais fixes",
    "cancellation_policy": "Não há reembolsos",
    "house_manager": {
        "name": "Alice Zqt",
        "phone_number": "+351920920920",
        "languages": [
            "Portuguese",
            "English"
        ]
    }
}

"""
