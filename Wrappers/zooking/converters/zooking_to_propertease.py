from ProjectUtils.MessagingService.schemas import Service
from Wrappers.base_wrapper.utils import invert_map
from Wrappers.models import set_and_get_property_internal_id, set_and_get_reservation_internal_id, \
    set_or_get_property_internal_id
from Wrappers.zooking.converters.propertease_to_zooking import ProperteaseToZooking


class ZookingToPropertease:
    bedroom_type_map = invert_map(ProperteaseToZooking.bedroom_type_map)
    fixtures_map = invert_map(ProperteaseToZooking.fixtures_map)
    amenities_map = invert_map(ProperteaseToZooking.amenities_map)

    @staticmethod
    def convert_property(zooking_property):
        propertease_property = dict()
        propertease_property["_id"] = set_and_get_property_internal_id(Service.ZOOKING, zooking_property.get("id"))
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
        bedrooms_converted = {}
        for name, beds in zooking_bedrooms.items():
            bedrooms_converted[name] = {
                "beds": [
                    {
                        "number_beds": bed.get("number_beds"),
                        "type": ZookingToPropertease.bedroom_type_map.get(
                            bed.get("bed_type")
                        ),
                    }
                    for bed in beds if bed.get("bed_type") in ZookingToPropertease.bedroom_type_map
                ]
            }
        return bedrooms_converted

    @staticmethod
    def convert_bathrooms(zooking_bathrooms):
        bathrooms_converted = {}
        for bathroom in zooking_bathrooms:
            bathrooms_converted[bathroom.get("name")] = {
                "fixtures": [
                    ZookingToPropertease.fixtures_map[zook_fixture]
                    for zook_fixture in bathroom.get("bathroom_fixtures")
                ]
            }
        return bathrooms_converted

    @staticmethod
    def convert_amenities(zooking_amenities):
        # there might be amenities in zooking that don't exist in propertease,
        return [
            ZookingToPropertease.amenities_map[zook_amen]
            for zook_amen in zooking_amenities
            if zook_amen in ZookingToPropertease.amenities_map.keys()
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

    @staticmethod
    def convert_reservation(zooking_reservation, owner_email: str):
        print("\nzooking_reservation", zooking_reservation)
        propertease_reservation = {
            "_id": set_and_get_reservation_internal_id(Service.ZOOKING, zooking_reservation.get("id")),
            "property_id": set_or_get_property_internal_id(Service.ZOOKING, zooking_reservation.get("property_id")),
            "owner_email": owner_email,
            "status": zooking_reservation.get("status"),
            "begin_datetime": zooking_reservation.get("arrival"),
            "end_datetime": zooking_reservation.get("departure"),
            "client_email": zooking_reservation.get("client_email"),
            "client_name": zooking_reservation.get("client_name"),
            "client_phone": zooking_reservation.get("client_phone"),
            "cost": zooking_reservation.get("cost"),
            "confirmed": zooking_reservation.get("confirmed"),
        }
        print("\npropertease_reservation", propertease_reservation)
        return propertease_reservation
