from datetime import datetime
from email import utils

from .exceptions import TimerNotStartedException, TimerNotFinishedException


class Timer:
    __started: bool = False
    __finished: bool = False

    def start(self) -> None:
        self.__start_timestamp = datetime.now().timestamp()
        self.__started = True  # [ ] with time zone

    def stop(self) -> None:
        if self.__started:
            self.__finish_timestamp = datetime.now().timestamp()
            self.__finished = True
        else:
            raise TimerNotStartedException

    @property
    def time_delta(self) -> datetime:
        if self.__finished:
            time_delta = self.__finish_timestamp - self.__start_timestamp
            return datetime.fromtimestamp(time_delta)
        else:
            raise TimerNotFinishedException

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
