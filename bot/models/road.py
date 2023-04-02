from tortoise import fields
from tortoise.models import Model


class PomodoroStats(Model):
    user_id = fields.IntField(pk=True)
    today_cnt = fields.IntField(default=0)
    total_cnt = fields.IntField(default=0)


class RoadSettings(Model):
    user_id = fields.IntField(pk=True)
    time_focused = fields.TimeField()
    time_relax = fields.TimeField()


# NOTE: unused
class Habits(Model):
    habit_id = fields.IntField(pk=True)
    user_id = fields.IntField()
    name = fields.TextField()
    notify_time = fields.TimeField()
