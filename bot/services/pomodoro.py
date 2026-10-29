from configs import db
from models.road import PomodoroStats


class Pomodoro:
    __model = PomodoroStats

    @classmethod
    async def increment_today_stat(cls, user_id: int) -> int:
        async with db.SessionLocal() as session:
            user = await session.get(cls.__model, user_id)

            if not user:
                user = cls.__model(user_id=user_id, today_cnt=1, total_cnt=0)
                session.add(user)
                cnt = 1
            else:
                user.today_cnt += 1
                cnt = user.today_cnt

            await session.commit()
            return cnt
