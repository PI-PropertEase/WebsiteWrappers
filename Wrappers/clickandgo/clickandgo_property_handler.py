from Wrappers.clickandgo.clickandgo_wrapper import CNGWrapper
from Wrappers.property_handler import run_property_handler

if __name__ == "__main__":
    run_property_handler(CNGWrapper("clickandgo_regular_queue"))
