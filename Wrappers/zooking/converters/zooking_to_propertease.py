import logging

from ProjectUtils.MessagingService.schemas import Service
from Wrappers.base_wrapper.utils import invert_map
from Wrappers.models import ReservationIdMapper, ReservationStatus
from Wrappers.crud import get_property_internal_id, set_property_internal_id, create_reservation, update_reservation
from Wrappers.zooking.converters.propertease_to_zooking import ProperteaseToZooking

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class ZookingToPropertease:
    service = ProperteaseToZooking.service
    bedroom_type_map = invert_map(ProperteaseToZooking.bedroom_type_map)
    fixtures_map = invert_map(ProperteaseToZooking.fixtures_map)
    amenities_map = invert_map(ProperteaseToZooking.amenities_map)

    @staticmethod
    def convert_property(zooking_property):
        LOGGER.debug("INPUT CONVERTING PROPERTY - Zooking property: %s", zooking_property)
        propertease_property = dict()
        propertease_property["_id"] = set_property_internal_id(ZookingToPropertease.service, zooking_property.get("id"))
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

        LOGGER.debug("OUTPUT CONVERTING PROPERTY - PropertEase property: %s", propertease_property)
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
    def convert_reservation(zooking_reservation, owner_email: str, reservation: ReservationIdMapper = None):
        LOGGER.debug("INPUT CONVERTING RESERVATIONS - Zooking reservation: %s", zooking_reservation)
        reservation_status = zooking_reservation.get("reservation_status")
        if reservation is not None:
            reservation_id = reservation.internal_id
            LOGGER.info("Existing reservation with status '%s' detected. New reservation status: '%s'", 
                        reservation.reservation_status, reservation_status)
            update_reservation(ZookingToPropertease.service, reservation_id, reservation_status)
        else:
            reservation_id = create_reservation(ZookingToPropertease.service, zooking_reservation.get("id"), reservation_status).internal_id

        propertease_reservation = {
            "_id": reservation_id,
            "reservation_status": reservation_status,
            "property_id": get_property_internal_id(ZookingToPropertease.service, zooking_reservation.get("property_id")),
            "owner_email": owner_email,
            "begin_datetime": zooking_reservation.get("arrival"),
            "end_datetime": zooking_reservation.get("departure"),
            "client_email": zooking_reservation.get("client_email"),
            "client_name": zooking_reservation.get("client_name"),
            "client_phone": zooking_reservation.get("client_phone"),
            "cost": zooking_reservation.get("cost"),
        }
        LOGGER.debug("OUTPUT CONVERTING RESERVATION - PropertEase reservation: %s", propertease_reservation)
        return propertease_reservation
