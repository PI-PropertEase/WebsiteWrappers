from abc import ABC, abstractmethod


# Interface of what a wrapper is able to do
class BaseAPIWrapper(ABC):
    @abstractmethod
    def create_property(self, property):
        pass

    @abstractmethod
    def update_property(self, property):
        pass

    @abstractmethod
    def delete_property(self, property):
        pass

    @abstractmethod
    def import_properties(self, user):
        pass
