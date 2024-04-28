from Wrappers.clickandgo.clickandgo_wrapper import CNGWrapper
from Wrappers.scheduled_events_handler import run_scheduled_events_handler


if __name__ == "__main__":
    run_scheduled_events_handler(CNGWrapper("clickandgo_scheduled_queue"))
