from abc import ABC, abstractmethod
from datetime import datetime

from ProjectUtils.MessagingService.schemas import Service as ServiceSchema


# Interface of what a wrapper is able to do
class BaseWrapper(ABC):
    def __init__(self, url: str, queue: str, service_schema: ServiceSchema) -> None:
        self.url = url
        self.queue = queue
        self.service_schema = service_schema

    @abstractmethod
    def create_property(self, property):
        pass

    @abstractmethod
    def update_property(self, prop_internal_id: int, prop_update_parameters: dict):
        pass

    @abstractmethod
    def delete_property(self, property):
        pass

    @abstractmethod
    def create_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: datetime, end_datetime: datetime):
        pass

    # @abstractmethod
    # def update_management_event(self, property_internal_id: int, event_internal_id: int, begin_datetime: datetime, end_datetime: datetime):
    #     pass

    @abstractmethod
    def import_properties(self, user):
        pass

    @abstractmethod
    def import_reservations(self, user):
        pass

    @abstractmethod
    def import_new_or_newly_canceled_reservations(self, user):
        pass

    @abstractmethod
    def confirm_reservation(self, reservation_internal_id):
        pass

    @abstractmethod
    def delete_reservation(self, reservation_internal_id):
        pass
