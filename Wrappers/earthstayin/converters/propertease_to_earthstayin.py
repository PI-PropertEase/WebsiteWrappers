import logging

from ProjectUtils.MessagingService.schemas import Service
from Wrappers.crud import get_property_external_id

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class ProperteaseToEarthstayin:
    service = Service.EARTHSTAYIN
    bedroom_type_map = {
        "single": "single_bed",
        "king": "king_bed",
        "queen": "queen_bed"
    }
    fixtures_map = {"bathtub": "tub", "shower": "shower", "toilet": "toilet", "bidet": "bidet"}
    amenities_map = {
        "air_conditioner": "AC",
        "free_wifi": "free_wifi",
        "parking_space": "car_parking",
    }
    commission = 0.05

    @staticmethod
    def convert_property(propertease_property):
        LOGGER.debug("INPUT CONVERTING PROPERTY - PropertEase property: %s", propertease_property)
        earthstayin_property = dict()
        property_id = earthstayin_property.get("_id")
        earthstayin_property["id"] = None if property_id is None else get_property_external_id(ProperteaseToEarthstayin.service,
                                                                                               property_id)
        earthstayin_property["user_email"] = propertease_property.get("user_email")
        earthstayin_property["name"] = propertease_property.get("title")
        earthstayin_property["address"] = propertease_property.get("address")
        earthstayin_property["description"] = propertease_property.get("description")
        earthstayin_property["curr_price"] = ProperteaseToEarthstayin.convert_price(
            propertease_price=propertease_property.get("price"),
            after_commission=propertease_property.get("after_commission")
        )
        earthstayin_property["number_of_guests"] = propertease_property.get("number_guests")
        earthstayin_property["square_meters"] = propertease_property.get("square_meters")
        earthstayin_property["bedrooms"] = None \
            if (propertease_bedrooms := propertease_property.get("bedrooms")) is None \
            else ProperteaseToEarthstayin.convert_bedrooms(propertease_bedrooms)
        earthstayin_property["bathrooms"] = None \
            if (propertease_bathrooms := propertease_property.get("bathrooms")) is None \
            else ProperteaseToEarthstayin.convert_bathrooms(propertease_bathrooms)
        earthstayin_property["available_amenities"] = None \
            if (propertease_amenities := propertease_property.get("amenities")) is None \
            else ProperteaseToEarthstayin.convert_amenities(propertease_amenities)
        earthstayin_property["house_rules"] = None \
            if (propertease_house_rules := propertease_property.get("house_rules")) is None \
            else ProperteaseToEarthstayin.convert_house_rules(propertease_house_rules)
        earthstayin_property["additional_info"], earthstayin_property["accessibilities"] = (None, None) \
            if (propertease_additional_info := propertease_property.get("additional_info")) is None \
            else ProperteaseToEarthstayin.convert_additional_info(propertease_additional_info)
        # the following elements are not supported in earthstayin -> no need to convert:
        # - cancellation_policy
        # - contacts
        LOGGER.debug("OUTPUT CONVERTING PROPERTY - Earthstayin property: %s", earthstayin_property)

        return earthstayin_property

    @staticmethod
    def convert_bedrooms(propertease_bedrooms):
        converted_bedrooms = {}
        for bedroom_name in propertease_bedrooms:
            converted_bedrooms[bedroom_name] = []
            for bed in propertease_bedrooms[bedroom_name]["beds"]:
                converted_bedrooms[bedroom_name].append({
                    "number_beds": bed.get("number_beds"),
                    "bed_type": ProperteaseToEarthstayin.bedroom_type_map.get(
                        bed.get("type")
                    ),
                })
        return converted_bedrooms

    @staticmethod
    def convert_bathrooms(propertease_bathrooms):
        converted_bathrooms = []
        for bathroom_name in propertease_bathrooms:
            converted_bathrooms.append({
                "name": bathroom_name,
                "bathroom_fixtures": [
                    converted_fixture for fixture in propertease_bathrooms[bathroom_name].get("fixtures")
                    if (converted_fixture := ProperteaseToEarthstayin.fixtures_map.get(fixture)) is not None
                ]
            })
        return converted_bathrooms

    @staticmethod
    def convert_amenities(propertease_amenities):
        return [
            converted_amenity for amenity in propertease_amenities
            if (converted_amenity := ProperteaseToEarthstayin.amenities_map.get(amenity)) is not None
        ]

    @staticmethod
    def convert_house_rules(propertease_houserules):
        check_in_parts = propertease_houserules.get("check_in")
        check_out_parts = propertease_houserules.get("check_out")
        rest_time_parts = propertease_houserules.get("rest_time")
        return {
            "checkin_time": f"{check_in_parts['begin_time']}-{check_in_parts['end_time']}",
            "checkout_time": f"{check_out_parts['begin_time']}-{check_out_parts['end_time']}",
            "smoking_allowed": propertease_houserules.get("smoking"),
            "rest_time": rest_time_parts['begin_time'],
            "pets_allowed": propertease_houserules.get("allow_pets")
        }

    @staticmethod
    def convert_additional_info(propertease_additional_info):
        additional_info_parts = propertease_additional_info.split(". This property has the following accessibilities: ")
        return additional_info_parts[0], additional_info_parts[-1].split(", ") if len(additional_info_parts) > 1 else []

    @staticmethod
    def convert_price(propertease_price: float, after_commission: bool) -> float:
        return propertease_price * (1 + ProperteaseToEarthstayin.commission) if after_commission else propertease_price 
