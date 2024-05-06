from ProjectUtils.MessagingService.schemas import Service
from Wrappers.crud import get_property_external_id


class ProperteaseToClickandgo:
    service = Service.CLICKANDGO
    bedroom_type_map = {
        "single": "single",
        "king": "king",
        "queen": "queen",
    }
    fixtures_map = {"bathtub": "tub", "shower": "shower", "toilet": "toilet"}
    amenities_map = {
        "air_conditioner": "AC",
        "free_wifi": "wifi_free",
        "parking_space": "parking",
    }
    commission = 0.02


    @staticmethod
    def convert_property(propertease_property):
        clickandgo_property = dict()
        property_id = clickandgo_property.get("_id")
        clickandgo_property["id"] = None if property_id is None else get_property_external_id(ProperteaseToClickandgo.service,
                                                                                              property_id)
        clickandgo_property["user_email"] = propertease_property.get("user_email")
        clickandgo_property["name"] = propertease_property.get("title")
        clickandgo_property["address"] = propertease_property.get("address")
        clickandgo_property["description"] = propertease_property.get("description")
        clickandgo_property["curr_price"] = ProperteaseToClickandgo.convert_price(
            propertease_price=propertease_property.get("price"),
            after_commission=propertease_property.get("after_commission")
        )
        clickandgo_property["guest_num"] = propertease_property.get("number_guests")
        clickandgo_property["house_area"] = propertease_property.get("square_meters")
        clickandgo_property["bedrooms"] = None \
            if (propertease_bedrooms := propertease_property.get("bedrooms")) is None \
            else ProperteaseToClickandgo.convert_bedrooms(propertease_bedrooms)
        clickandgo_property["bathrooms"] = None \
            if (propertease_bathrooms := propertease_property.get("bathrooms")) is None \
            else ProperteaseToClickandgo.convert_bathrooms(propertease_bathrooms)
        clickandgo_property["available_amenities"] = None \
            if (propertease_amenities := propertease_property.get("amenities")) is None \
            else ProperteaseToClickandgo.convert_amenities(propertease_amenities)
        clickandgo_property["house_rules"] = None \
            if (propertease_house_rules := propertease_property.get("house_rules")) is None \
            else ProperteaseToClickandgo.convert_house_rules(propertease_house_rules)
        clickandgo_property["additional_info"] = propertease_property.get("additional_info")
        clickandgo_property["house_manager"] = None \
            if (propertease_contacts := propertease_property.get("contacts")) is None \
            else ProperteaseToClickandgo.convert_contacts(propertease_contacts)
        # the following elements are not supported in clickandgo -> no need to convert:
        # - cancellation_policy
        print(f"\npropertease_property {propertease_property}\n")
        print(f"clickandgo_property {clickandgo_property}\n")
        return clickandgo_property

    @staticmethod
    def convert_bedrooms(propertease_bedrooms):
        converted_bedrooms = {}
        for bedroom_name in propertease_bedrooms:
            converted_bedrooms[bedroom_name] = []
            for bed in propertease_bedrooms[bedroom_name]["beds"]:
                converted_bedrooms[bedroom_name].append({
                    "number_beds": bed.get("number_beds"),
                    "bed_type": ProperteaseToClickandgo.bedroom_type_map.get(
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
                    if (converted_fixture := ProperteaseToClickandgo.fixtures_map.get(fixture)) is not None
                ]
            })
        return converted_bathrooms

    @staticmethod
    def convert_amenities(propertease_amenities):
        return [
            converted_amenity for amenity in propertease_amenities
            if (converted_amenity := ProperteaseToClickandgo.amenities_map.get(amenity)) is not None
        ]

    @staticmethod
    def convert_house_rules(propertease_houserules):
        check_in_parts = propertease_houserules.get("check_in")
        check_out_parts = propertease_houserules.get("check_out")
        rest_time_parts = propertease_houserules.get("rest_time")
        return {
            "check_in": f"{check_in_parts['begin_time']}-{check_in_parts['end_time']}",
            "check_out": f"{check_out_parts['begin_time']}-{check_out_parts['end_time']}",
            "smoking_allowed": propertease_houserules.get("smoking"),
            "parties_allowed": propertease_houserules.get("parties"),
            "rest_time": f"{rest_time_parts['begin_time']}-{rest_time_parts['end_time']}",
            "pets_allowed": propertease_houserules.get("allow_pets")
        }

    @staticmethod
    def convert_contacts(propertease_contacts):
        return {
                "name": propertease_contacts[0].get("name"),
                "phone_number": propertease_contacts[0].get("phone_number"),
                "languages": []
            } if len(propertease_contacts) > 0 else {}

    @staticmethod
    def convert_price(propertease_price: float, after_commission: bool) -> float:
        return propertease_price * (1 + ProperteaseToClickandgo.commission) if after_commission else propertease_price 
