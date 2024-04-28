from Wrappers.earthstayin.earthstayin_wrapper import EarthStayinWrapper
from Wrappers.regular_events_handler import run_regular_events_handler

if __name__ == "__main__":
    run_regular_events_handler(EarthStayinWrapper("earthstayin_regular_queue"))
