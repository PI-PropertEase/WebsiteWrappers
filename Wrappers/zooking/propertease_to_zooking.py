"""
    Converts property from the PropertEase schema to Zooking API
"""
from ProjectUtils.MessagingService.schemas import Service
from Wrappers.models import get_property_external_id


def property_from_propertease_to_zooking(propertease_property):
    zooking_property = dict()
    property_id = zooking_property.get("_id")
    zooking_property["id"] = None if property_id is None else get_property_external_id(Service.ZOOKING,
                                                                                              property_id)
    zooking_property["user_email"] = propertease_property.get("user_email")
    zooking_property["name"] = propertease_property.get("title")
    zooking_property["address"] = propertease_property.get("address")
    zooking_property["description"] = propertease_property.get("description")
    zooking_property["curr_price"] = propertease_property.get("price")
    zooking_property["number_of_guests"] = propertease_property.get("number_guests")
    zooking_property["square_meters"] = propertease_property.get("square_meters")
    zooking_property["bedrooms"] = None \
        if (propertease_bedrooms := propertease_to_zooking_bedrooms(propertease_property.get("bedrooms"))) is None \
        else propertease_bedrooms
    zooking_property["bathrooms"] = None \
        if (propertease_bathrooms := propertease_property.get("bathrooms")) is None \
        else propertease_to_zooking_bathrooms(propertease_bathrooms)
    zooking_property["amenities"] = None \
        if (propertease_amenities := propertease_property.get("amenities")) is None \
        else propertease_to_zooking_amenities(propertease_amenities)
    zooking_property["additional_info"] = propertease_property.get("additional_info")
    # the following elements are not supported in zooking -> no need to convert:
    # - house rules
    # - cancellation_policy
    # - contacts
    print(f"\npropertease_property {propertease_property}\n")
    print(f"zooking_property {zooking_property}\n")
    return zooking_property


def propertease_to_zooking_bedrooms(propertease_bedrooms):
    bedroom_type_map = {
        "single": "single_bed",
        "king": "king_bed",
        "queen": "queen_bed",
    }
    converted_bedrooms = {}
    for bedroom_name in propertease_bedrooms:
        converted_bedrooms[bedroom_name] = []
        for bed in propertease_bedrooms[bedroom_name]["beds"]:
            converted_bedrooms[bedroom_name].append({
                "number_beds": bed.get("number_beds"),
                "bed_type": bedroom_type_map.get(
                    bed.get("type")
                ),
            })
    return converted_bedrooms


def propertease_to_zooking_bathrooms(propertease_bathrooms):
    fixtures_map = {"bathtub": "tub", "shower": "shower", "toilet": "toilet"}
    converted_bathrooms = []
    for bathroom_name in propertease_bathrooms:
        converted_bathrooms.append({
            "name": bathroom_name,
            "bathroom_fixtures": [
                converted_fixture for fixture in propertease_bathrooms[bathroom_name].get("fixtures")
                if (converted_fixture := fixtures_map.get(fixture)) is not None
            ]
        })
    return converted_bathrooms


def propertease_to_zooking_amenities(propertease_amenities):
    amenities_map = {
        "air_conditioner": "AC",
        "free_wifi": "wifi",
        "parking_space": "open_parking",
    }
    return [
        converted_amenity for amenity in propertease_amenities
        if (converted_amenity := amenities_map.get(amenity)) is not None
    ]
