import logging

from ProjectUtils.MessagingService.schemas import Service
from Wrappers.base_wrapper.utils import invert_map
from Wrappers.clickandgo.converters.propertease_to_clickandgo import ProperteaseToClickandgo
from Wrappers.models import ReservationIdMapper, ReservationStatus
from Wrappers.crud import get_property_internal_id, set_property_internal_id, create_reservation, update_reservation

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class ClickandgoToPropertease:
    service = ProperteaseToClickandgo.service
    bedroom_type_map = invert_map(ProperteaseToClickandgo.bedroom_type_map)
    fixtures_map = invert_map(ProperteaseToClickandgo.fixtures_map)
    amenities_map = invert_map(ProperteaseToClickandgo.amenities_map)

    @staticmethod
    def convert_property(clickandgo_property):
        LOGGER.debug("INPUT CONVERTING PROPERTY - ClickAndGo property: %s", clickandgo_property)
        propertease_property = {}
        propertease_property["_id"] = set_property_internal_id(ClickandgoToPropertease.service, clickandgo_property.get("id"))
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
            clickandgo_property.get("house_managers")
        )

        LOGGER.debug("OUTPUT CONVERTING PROPERTY - PropertEase property: %s", propertease_property)
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
    def convert_contacts(clickandgo_housemanagers):
        propertease_contacts = []
        for house_manager in clickandgo_housemanagers:
            propertease_contacts.append({
                "name": house_manager.get("name"),
                "phone_number": house_manager.get("phone_number")
            })
        return propertease_contacts

    @staticmethod
    def convert_reservation(clickandgo_reservation, owner_email: str, reservation: ReservationIdMapper = None):
        LOGGER.debug("INPUT CONVERTING RESERVATIONS - ClickAndGo reservation: %s", clickandgo_reservation)
        reservation_status = clickandgo_reservation.get("reservation_status")
        if reservation is not None:
            reservation_id = reservation.internal_id
            LOGGER.info("Existing reservation with status '%s' detected. New reservation status: '%s'", 
                        reservation.reservation_status, reservation_status)
            update_reservation(ClickandgoToPropertease.service, reservation_id, reservation_status)
        else:
            reservation_id = create_reservation(ClickandgoToPropertease.service, clickandgo_reservation.get("id"), reservation_status).internal_id

        propertease_reservation = {
            "_id": reservation_id,
            "reservation_status": reservation_status,
            "property_id": get_property_internal_id(ClickandgoToPropertease.service, clickandgo_reservation.get("property_id")),
            "owner_email": owner_email,
            "begin_datetime": clickandgo_reservation.get("arrival"),
            "end_datetime": clickandgo_reservation.get("departure"),
            "client_email": clickandgo_reservation.get("client_email"),
            "client_name": clickandgo_reservation.get("client_name"),
            "client_phone": clickandgo_reservation.get("client_phone"),
            "cost": clickandgo_reservation.get("cost"),
        }
        LOGGER.debug("OUTPUT CONVERTING RESERVATION - PropertEase reservation: %s", propertease_reservation)
        return propertease_reservation

