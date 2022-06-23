class TimerNotStartedException(Exception):
    def __str__(self) -> str:
        return 'Timer not started'


class TimerNotFinishedException(Exception):
    def __str__(self) -> str:
        return 'Timer not finished'
