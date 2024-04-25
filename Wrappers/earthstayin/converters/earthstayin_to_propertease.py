from ProjectUtils.MessagingService.schemas import Service
from Wrappers.base_wrapper.utils import invert_map
from Wrappers.earthstayin.converters.propertease_to_earthstayin import ProperteaseToEarthstayin
from Wrappers.models import set_property_internal_id, set_and_get_reservation_internal_id, \
    set_or_get_property_internal_id


class EarthstayinToPropertease:
    bedroom_type_map = invert_map(ProperteaseToEarthstayin.bedroom_type_map)
    fixtures_map = invert_map(ProperteaseToEarthstayin.fixtures_map)
    amenities_map = invert_map(ProperteaseToEarthstayin.amenities_map)

    @staticmethod
    def convert_property(earthstayin_property):
        propertease_property = {}
        propertease_property["_id"] = set_property_internal_id(Service.EARTHSTAYIN,
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
        bedrooms_converted = {}
        for name, beds in earthstayin_bedrooms.items():
            bedrooms_converted[name] = {
                "beds": [
                    {
                        "number_beds": bed.get("number_beds"),
                        "type": EarthstayinToPropertease.bedroom_type_map.get(
                            bed.get("bed_type")
                        ),
                    }
                    for bed in beds if bed.get("bed_type") in EarthstayinToPropertease.bedroom_type_map
                ]
            }
        return bedrooms_converted

    @staticmethod
    def convert_bathrooms(earthstayin_bathrooms):
        bathrooms_converted = {}
        for bathroom in earthstayin_bathrooms:
            bathrooms_converted[bathroom.get("name")] = {
                "fixtures": [
                    EarthstayinToPropertease.fixtures_map[earthstayin_fixture]
                    for earthstayin_fixture in bathroom.get("bathroom_fixtures")
                ]
            }
        return bathrooms_converted

    @staticmethod
    def convert_amenities(earthstayin_amenities):
        # there might be amenities in earthstayin that don't exist in propertease,
        return [
            EarthstayinToPropertease.amenities_map[cng_amen]
            for cng_amen in earthstayin_amenities
            if cng_amen in EarthstayinToPropertease.amenities_map.keys()
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

    @staticmethod
    def convert_reservation(earthstayin_reservation, owner_email: str):
        print("\nearthstayin_reservation", earthstayin_reservation)
        propertease_reservation = {
            "_id": set_and_get_reservation_internal_id(Service.EARTHSTAYIN, earthstayin_reservation.get("id")),
            "property_id": set_or_get_property_internal_id(Service.EARTHSTAYIN, earthstayin_reservation.get("property_id")),
            "owner_email": owner_email,
            "status": earthstayin_reservation.get("status"),
            "begin_datetime": earthstayin_reservation.get("arrival"),
            "end_datetime": earthstayin_reservation.get("departure"),
            "client_email": earthstayin_reservation.get("client_email"),
            "client_name": earthstayin_reservation.get("client_name"),
            "client_phone": earthstayin_reservation.get("client_phone"),
            "cost": earthstayin_reservation.get("cost"),
            "reservation_status": earthstayin_reservation.get("reservation_status"),
        }
        print("\npropertease_reservation", propertease_reservation)
        return propertease_reservation
