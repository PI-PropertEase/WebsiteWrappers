from Wrappers.earthstayin.earthstayin_wrapper import EarthStayinWrapper
from Wrappers.scheduled_events_handler import run_scheduled_events_handler


if __name__ == "__main__":
    run_scheduled_events_handler(EarthStayinWrapper("earthstayin_scheduled_queue"))
