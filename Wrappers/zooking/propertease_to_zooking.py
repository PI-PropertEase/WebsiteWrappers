"""
    Converts property from the PropertEase schema to Zooking API
"""
from ProjectUtils.MessagingService.schemas import Service
from Wrappers.models import get_property_external_id


def property_from_propertease_to_zooking(propertease_property):
    zooking_property = dict()
    print("\npropertease_property\n", propertease_property)
    property_id = zooking_property.get("_id")
    zooking_property["id"] = property_id if property_id is None else get_property_external_id(Service.ZOOKING,
                                                                                              property_id)
    zooking_property["user_email"] = propertease_property.get("user_email")
    zooking_property["name"] = propertease_property.get("title")
    zooking_property["address"] = propertease_property.get("address")
    zooking_property["description"] = propertease_property.get("description")
    zooking_property["curr_price"] = propertease_property.get("price")
    zooking_property["number_guests"] = propertease_property.get("number_guests")
    zooking_property["square_meters"] = propertease_property.get("square_meters")
    propertease_to_zooking_bedroom(propertease_property.get("bedrooms"))

    # propertease_property["bedrooms"] = self.zooking_to_propertease_bedroom(
    #     zooking_property.get("bedrooms")
    # )
    # propertease_property["bathrooms"] = self.zooking_to_propertease_bathroom(
    #     zooking_property.get("bathrooms")
    # )
    # propertease_property["amenities"] = self.zooking_to_propertease_amenities(
    #     zooking_property.get("amenities")
    # )
    # # not supported in zooking
    # propertease_property["house_rules"] = (
    #     self.empty_house_rules()
    # )
    # propertease_property["additional_info"] = zooking_property.get(
    #     "additional_info"
    # )
    # propertease_property["cancellation_policy"] = ""  # not supported in zooking
    # propertease_property["contacts"] = []  # not supported in Zooking


def propertease_to_zooking_bedroom(propertease_bedrooms):
    bedroom_type_map = {
        "single": "single_bed",
        "king": "king_bed",
        "queen": "queen_bed",
    }
    print("propertease_bedrooms: ", propertease_bedrooms)
    converted_bedrooms = []
    for i in range(len(propertease_bedrooms)):
        converted_bedrooms.append([])
        for bed in propertease_bedrooms[i]["beds"]:
            converted_bedrooms[i].append({
                "number_beds": bed.get("number_beds"),
                "type": bedroom_type_map.get(bed.get("type"))
            })
    print("converted_bedrooms", converted_bedrooms)