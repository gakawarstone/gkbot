from models.road import PomodoroStats


class Pomodoro:
    __model = PomodoroStats

    @classmethod
    async def increment_today_stat(cls, user_id: int) -> int:
        user, _ = await cls.__model.get_or_create(user_id=user_id)
        cnt = user.today_cnt + 1
        await cls.__model.filter(user_id=user.user_id).update(today_cnt=cnt)
        return cnt
