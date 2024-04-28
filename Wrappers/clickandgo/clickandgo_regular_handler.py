from Wrappers.clickandgo.clickandgo_wrapper import CNGWrapper
from Wrappers.regular_events_handler import run_regular_events_handler

if __name__ == "__main__":
    run_regular_events_handler(CNGWrapper("clickandgo_regular_queue"))
