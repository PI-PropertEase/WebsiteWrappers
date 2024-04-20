from ProjectUtils.MessagingService.schemas import Service
from Wrappers.models import get_property_mapped_id


class ZookingToPropertease:

    @staticmethod
    def convert_property(zooking_property):
        propertease_property = dict()
        propertease_property["_id"] = get_property_mapped_id(Service.ZOOKING, zooking_property.get("id"))
        propertease_property["user_email"] = zooking_property.get("user_email")
        propertease_property["title"] = zooking_property.get("name")
        propertease_property["address"] = zooking_property.get("address")
        propertease_property["description"] = zooking_property.get("description")
        propertease_property["price"] = zooking_property.get("curr_price")
        propertease_property["number_guests"] = zooking_property.get("number_of_guests")
        propertease_property["square_meters"] = zooking_property.get("square_meters")
        propertease_property["bedrooms"] = ZookingToPropertease.convert_bedrooms(
            zooking_property.get("bedrooms")
        )
        propertease_property["bathrooms"] = ZookingToPropertease.convert_bathrooms(
            zooking_property.get("bathrooms")
        )
        propertease_property["amenities"] = ZookingToPropertease.convert_amenities(
            zooking_property.get("amenities")
        )
        # not supported in zooking
        propertease_property["house_rules"] = (
            ZookingToPropertease.empty_house_rules()
        )
        propertease_property["additional_info"] = zooking_property.get(
            "additional_info"
        )
        propertease_property["cancellation_policy"] = ""  # not supported in zooking
        propertease_property["contacts"] = []  # not supported in Zooking

        return propertease_property

    @staticmethod
    def convert_bedrooms(zooking_bedrooms):
        bedroom_type_map = {
            "single_bed": "single",
            "king_bed": "king",
            "queen_bed": "queen",
        }

        bedrooms_converted = {}
        for name, beds in zooking_bedrooms.items():
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
    def convert_bathrooms(zooking_bathrooms):
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

    @staticmethod
    def convert_amenities(zooking_amenities):
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

    @staticmethod
    def empty_house_rules():
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

