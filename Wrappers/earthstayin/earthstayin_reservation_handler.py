from Wrappers.earthstayin.earthstayin_wrapper import EarthStayinWrapper
from Wrappers.reservation_handler import run_reservation_handler


if __name__ == "__main__":
    run_reservation_handler(EarthStayinWrapper())
