import requests
from ..base_wrapper.api_wrapper import BaseAPIWrapper


class ZookingAPIWrapper(BaseAPIWrapper):
    def __init__(self) -> None:
        super().__init__()
        self.url = "http://localhost:8000/"

    def create_property(self, property):
        url = self.url + "properties"
        print("Creating property...")
        requests.post(url=url, json=property)

    def update_property(self, property):
        _id = property.get("id")
        url = self.url + f"properties/{_id}"
        print("Updating property...")
        requests.put(url=url, json=property)

    def delete_property(self, property):
        _id = property.get("id")
        print("Deleting property...")
        url = self.url + f"properties/{_id}"
        requests.delete(url=url)
