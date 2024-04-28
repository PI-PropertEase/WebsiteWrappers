from Wrappers.regular_events_handler import run_regular_events_handler
from .zooking_wrapper import ZookingWrapper

if __name__ == "__main__":
    run_regular_events_handler(ZookingWrapper(queue="zooking_regular_queue"))
