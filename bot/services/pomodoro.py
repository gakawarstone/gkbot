from sqlalchemy import select
from configs import db
from models.road import PomodoroStats


class Pomodoro:
    __model = PomodoroStats

    @classmethod
    async def increment_today_stat(cls, user_id: int) -> int:
        async with db.SessionLocal() as session:
            stmt = select(cls.__model).where(cls.__model.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                user = cls.__model(user_id=user_id, today_cnt=1, total_cnt=0)
                session.add(user)
                cnt = 1
            else:
                user.today_cnt += 1
                cnt = user.today_cnt
            
            await session.commit()
            return cnt
