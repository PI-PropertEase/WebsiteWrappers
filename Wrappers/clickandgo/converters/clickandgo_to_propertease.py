from ProjectUtils.MessagingService.schemas import Service
from Wrappers.base_wrapper.utils import invert_map
from Wrappers.clickandgo.converters.propertease_to_clickandgo import ProperteaseToClickandgo
from Wrappers.models import set_and_get_property_internal_id, set_and_get_reservation_internal_id, \
    set_or_get_property_internal_id


class ClickandgoToPropertease:
    bedroom_type_map = invert_map(ProperteaseToClickandgo.bedroom_type_map)
    fixtures_map = invert_map(ProperteaseToClickandgo.fixtures_map)
    amenities_map = invert_map(ProperteaseToClickandgo.amenities_map)

    @staticmethod
    def convert_property(clickandgo_property):
        propertease_property = {}
        propertease_property["_id"] = set_and_get_property_internal_id(Service.CLICKANDGO, clickandgo_property.get("id"))
        propertease_property["user_email"] = clickandgo_property.get("user_email")
        propertease_property["title"] = clickandgo_property.get("name")
        propertease_property["address"] = clickandgo_property.get("address")
        propertease_property["description"] = clickandgo_property.get("description")
        propertease_property["price"] = clickandgo_property.get("curr_price")
        propertease_property["number_guests"] = clickandgo_property.get("guest_num")
        propertease_property["square_meters"] = clickandgo_property.get("house_area")
        propertease_property["bedrooms"] = ClickandgoToPropertease.convert_bedrooms(
            clickandgo_property.get("bedrooms")
        )
        propertease_property["bathrooms"] = ClickandgoToPropertease.convert_bathrooms(
            clickandgo_property.get("bathrooms")
        )
        propertease_property["amenities"] = ClickandgoToPropertease.convert_amenities(
            clickandgo_property.get("available_amenities")
        )
        propertease_property["house_rules"] = ClickandgoToPropertease.convert_house_rules(
            clickandgo_property.get("house_rules")
        )
        propertease_property["additional_info"] = clickandgo_property.get("additional_info")
        propertease_property["cancellation_policy"] = ""  # not supported in clickandgo
        propertease_property["contacts"] = ClickandgoToPropertease.convert_contacts(
            clickandgo_property.get("house_manager")
        )

        return propertease_property

    @staticmethod
    def convert_bedrooms(clickandgo_bedrooms):
        bedrooms_converted = {}
        for name, beds in clickandgo_bedrooms.items():
            bedrooms_converted[name] = {
                "beds": [
                    {
                        "number_beds": bed.get("number_beds"),
                        "type": ClickandgoToPropertease.bedroom_type_map.get(
                            bed.get("bed_type")
                        ),
                    }
                    for bed in beds if bed.get("bed_type") in ClickandgoToPropertease.bedroom_type_map
                ]
            }
        return bedrooms_converted

    @staticmethod
    def convert_bathrooms(clickandgo_bathrooms):
        bathrooms_converted = {}
        for bathroom in clickandgo_bathrooms:
            bathrooms_converted[bathroom.get("name")] = {
                "fixtures": [
                    ClickandgoToPropertease.fixtures_map[cng_fixture]
                    for cng_fixture in bathroom.get("bathroom_fixtures")
                ]
            }
        return bathrooms_converted

    @staticmethod
    def convert_amenities(clickandgo_amenities):
        # there might be amenities in clickandgo that don't exist in propertease,
        return [
            ClickandgoToPropertease.amenities_map[cng_amen]
            for cng_amen in clickandgo_amenities
            if cng_amen in ClickandgoToPropertease.amenities_map.keys()
        ]

    @staticmethod
    def convert_house_rules(clickandgo_houserules):
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

    @staticmethod
    def convert_contacts(clickandgo_housemanager):
        return [
            {
                "name": clickandgo_housemanager.get("name"),
                "phone_number": clickandgo_housemanager.get("phone_number"),
            }
        ]

    @staticmethod
    def convert_reservation(clickandgo_reservation, owner_email: str):
        print("\nclickandgo_reservation", clickandgo_reservation)
        propertease_reservation = {
            "_id": set_and_get_reservation_internal_id(Service.CLICKANDGO, clickandgo_reservation.get("id")),
            "property_id": set_or_get_property_internal_id(Service.CLICKANDGO, clickandgo_reservation.get("property_id")),
            "owner_email": owner_email,
            "status": clickandgo_reservation.get("status"),
            "begin_datetime": clickandgo_reservation.get("arrival"),
            "end_datetime": clickandgo_reservation.get("departure"),
            "client_email": clickandgo_reservation.get("client_email"),
            "client_name": clickandgo_reservation.get("client_name"),
            "client_phone": clickandgo_reservation.get("client_phone"),
            "cost": clickandgo_reservation.get("cost"),
            "confirmed": clickandgo_reservation.get("confirmed"),
        }
        print("\npropertease_reservation", propertease_reservation)
        return propertease_reservation

