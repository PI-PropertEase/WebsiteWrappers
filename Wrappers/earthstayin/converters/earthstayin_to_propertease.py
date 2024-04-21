from ProjectUtils.MessagingService.schemas import Service
from Wrappers.models import set_and_get_property_internal_id


class EarthstayinToPropertease:

    @staticmethod
    def convert_property(earthstayin_property):
        propertease_property = {}
        propertease_property["_id"] = set_and_get_property_internal_id(Service.EARTHSTAYIN,
                                                                       earthstayin_property.get("id"))
        propertease_property["user_email"] = earthstayin_property.get("user_email")
        propertease_property["title"] = earthstayin_property.get("name")
        propertease_property["address"] = earthstayin_property.get("address")
        propertease_property["description"] = earthstayin_property.get("description")
        propertease_property["price"] = earthstayin_property.get("curr_price")
        propertease_property["number_guests"] = earthstayin_property.get("number_of_guests")
        propertease_property["square_meters"] = earthstayin_property.get("square_meters")
        propertease_property["bedrooms"] = EarthstayinToPropertease.convert_bedrooms(
            earthstayin_property.get("bedrooms")
        )
        propertease_property["bathrooms"] = EarthstayinToPropertease.convert_bathrooms(
            earthstayin_property.get("bathrooms")
        )
        propertease_property["amenities"] = EarthstayinToPropertease.convert_amenities(
            earthstayin_property.get("amenities")
        )
        propertease_property["house_rules"] = EarthstayinToPropertease.convert_house_rules(
            earthstayin_property.get("house_rules")
        )
        propertease_property["additional_info"] = earthstayin_property.get("additional_info") + \
            ". This property has the following accessibilities: " + ", ".join(earthstayin_property.get("accessibilities"))
        propertease_property["cancellation_policy"] = ""  # not supported in earthstayin
        propertease_property["contacts"] = []  # not supported in earthstayin

        return propertease_property

    @staticmethod
    def convert_bedrooms(earthstayin_bedrooms):
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

    @staticmethod
    def convert_bathrooms(earthstayin_bathrooms):
        fixtures_map = {"tub": "bathtub", "shower": "shower", "toilet": "toilet", "bidet": "bidet"}
        bathrooms_converted = {}
        for bathroom in earthstayin_bathrooms:
            bathrooms_converted[bathroom.get("name")] = {
                "fixtures": [
                    fixtures_map[earthstayin_fixture]
                    for earthstayin_fixture in bathroom.get("bathroom_fixtures")
                ]
            }
        return bathrooms_converted

    @staticmethod
    def convert_amenities(earthstayin_amenities):
        amenities_map = {
            "AC": "air_conditioner",
            "free_wifi": "free_wifi",
            "car_parking": "parking_space",
        }
        # there might be amenities in earthstayin that don't exist in propertease,
        return [
            amenities_map[cng_amen]
            for cng_amen in earthstayin_amenities
            if cng_amen in amenities_map.keys()
        ]

    @staticmethod
    def convert_house_rules(earthstayin_houserules):
        check_in_parts = earthstayin_houserules.get("checkin_time").split("-")
        check_out_parts = earthstayin_houserules.get("checkout_time").split("-")
        return {
            "check_in": {
                "begin_time": check_in_parts[0],
                "end_time": check_in_parts[1],
            },
            "check_out": {
                "begin_time": check_out_parts[0],
                "end_time": check_out_parts[1],
            },
            "smoking": earthstayin_houserules.get("smoking_allowed"),
            "parties": False,
            "rest_time": {
                "begin_time": earthstayin_houserules.get("rest_time"),
                "end_time": "08:00",
            },
            "allow_pets": earthstayin_houserules.get("pets_allowed"),
        }
