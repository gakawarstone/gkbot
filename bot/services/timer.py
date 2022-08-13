from datetime import datetime
from email import utils

from .exceptions import TimerNotStartedException, TimerNotFinishedException


class Timer:
    def __init__(self) -> None:
        self.__started: bool = False
        self.__finished: bool = False

    def start(self) -> None:
        self.__start_timestamp = datetime.now().timestamp()
        self.__started = True  # [ ] with time zone

    def stop(self) -> None:
        if not self.__started:
            raise TimerNotStartedException
        self.__finish_timestamp = datetime.now().timestamp()
        self.__finished = True

    @property
    def time_delta(self) -> datetime:
        if not self.__finished:
            raise TimerNotFinishedException
        time_delta = self.__finish_timestamp - self.__start_timestamp
        return datetime.fromtimestamp(time_delta)

    @property
    def start_time_rfc2882(self) -> str:
        if self.__started:
            return self.__format_to_rfc2882_from_timestamp(
                self.__start_timestamp)
        else:
            raise TimerNotStartedException

    @property
    def finish_time_rfc2882(self) -> str:
        if self.__finished:
            return self.__format_to_rfc2882_from_timestamp(
                self.__finish_timestamp)
        else:
            raise TimerNotFinishedException

    @staticmethod
    def __format_to_rfc2882_from_timestamp(timestamp: float) -> str:
        return utils.format_datetime(datetime.fromtimestamp(timestamp))


class TimersManager:
    __timers: dict[str, Timer] = {}

    @classmethod
    def get_or_create_timer(cls, id: str) -> Timer:
        if id not in cls.__timers:
            cls.__timers[id] = Timer()
        return cls.__timers[id]

    @classmethod
    def get_timer_by_id(cls, id: str) -> Timer | None:
        if id not in cls.__timers:
            return None
        return cls.__timers[id]

    @classmethod
    def delete_timer_by_id(cls, id: str) -> None:
        cls.__timers.pop(id)
