from Wrappers.property_handler import run_property_handler
from .zooking_wrapper import ZookingWrapper

if __name__ == "__main__":
    run_property_handler(ZookingWrapper(queue="zooking_regular_queue"))
