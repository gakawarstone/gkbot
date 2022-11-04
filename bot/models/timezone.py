from tortoise import fields
from tortoise.models import Model


class TimeZone(Model):
    user_id = fields.IntField(pk=True)
    tz = fields.TimeDeltaField()
