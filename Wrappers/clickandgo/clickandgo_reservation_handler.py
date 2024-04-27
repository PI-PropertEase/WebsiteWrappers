from Wrappers.clickandgo.clickandgo_wrapper import CNGWrapper
from Wrappers.reservation_handler import run_reservation_handler


if __name__ == "__main__":
    run_reservation_handler(CNGWrapper())
