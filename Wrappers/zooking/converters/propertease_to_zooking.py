from ProjectUtils.MessagingService.schemas import Service
from Wrappers.crud import get_property_external_id


class ProperteaseToZooking:
    service = Service.ZOOKING
    bedroom_type_map = {
        "single": "single_bed",
        "king": "king_bed",
        "queen": "queen_bed",
    }
    fixtures_map = {"bathtub": "tub", "shower": "shower", "toilet": "toilet"}
    amenities_map = {
        "air_conditioner": "AC",
        "free_wifi": "wifi",
        "parking_space": "open_parking",
    }
    commission = 0.03

    @staticmethod
    def convert_property(propertease_property):
        zooking_property = dict()
        property_id = zooking_property.get("_id")
        zooking_property["id"] = None if property_id is None else get_property_external_id(ProperteaseToZooking.service,
                                                                                           property_id)
        zooking_property["user_email"] = propertease_property.get("user_email")
        zooking_property["name"] = propertease_property.get("title")
        zooking_property["address"] = propertease_property.get("address")
        zooking_property["description"] = propertease_property.get("description")
        zooking_property["curr_price"] = ProperteaseToZooking.convert_price(
            propertease_price=propertease_property.get("price"),
            after_commission=propertease_property.get("after_commission")
        )
        zooking_property["number_of_guests"] = propertease_property.get("number_guests")
        zooking_property["square_meters"] = propertease_property.get("square_meters")
        zooking_property["bedrooms"] = None \
            if (propertease_bedrooms := propertease_property.get("bedrooms")) is None \
            else ProperteaseToZooking.convert_bedrooms(propertease_bedrooms)
        zooking_property["bathrooms"] = None \
            if (propertease_bathrooms := propertease_property.get("bathrooms")) is None \
            else ProperteaseToZooking.convert_bathrooms(propertease_bathrooms)
        zooking_property["amenities"] = None \
            if (propertease_amenities := propertease_property.get("amenities")) is None \
            else ProperteaseToZooking.convert_amenities(propertease_amenities)
        zooking_property["additional_info"] = propertease_property.get("additional_info")
        zooking_property["closed_time_frames"] = propertease_property.get("closed_time_frames")
        # the following elements are not supported in zooking -> no need to convert:
        # - house rules
        # - cancellation_policy
        # - contacts
        print(f"\npropertease_property {propertease_property}\n")
        print(f"zooking_property {zooking_property}\n")
        return zooking_property

    @staticmethod
    def convert_bedrooms(propertease_bedrooms):
        converted_bedrooms = {}
        for bedroom_name in propertease_bedrooms:
            converted_bedrooms[bedroom_name] = []
            for bed in propertease_bedrooms[bedroom_name]["beds"]:
                converted_bedrooms[bedroom_name].append({
                    "number_beds": bed.get("number_beds"),
                    "bed_type": ProperteaseToZooking.bedroom_type_map.get(
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
                    if (converted_fixture := ProperteaseToZooking.fixtures_map.get(fixture)) is not None
                ]
            })
        return converted_bathrooms

    @staticmethod
    def convert_amenities(propertease_amenities):
        return [
            converted_amenity for amenity in propertease_amenities
            if (converted_amenity := ProperteaseToZooking.amenities_map.get(amenity)) is not None
        ]
    
    @staticmethod
    def convert_price(propertease_price: float, after_commission: bool) -> float:
        return propertease_price * (1 + ProperteaseToZooking.commission) if after_commission else propertease_price 
