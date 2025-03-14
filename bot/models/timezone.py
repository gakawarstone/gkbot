from tortoise import fields
from tortoise.models import Model


class TimeZone(Model):
    user_id = fields.IntField(primary_key=True)
    tz = fields.TimeDeltaField()
