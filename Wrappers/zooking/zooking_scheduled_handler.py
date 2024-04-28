from Wrappers.scheduled_events_handler import run_scheduled_events_handler
from .zooking_wrapper import ZookingWrapper


if __name__ == "__main__":
    run_scheduled_events_handler(ZookingWrapper("zooking_scheduled_queue"))
