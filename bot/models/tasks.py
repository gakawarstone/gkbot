from tortoise import fields
from tortoise.models import Model


class Task(Model):
    datetime = fields.DatetimeField()
    callback = fields.BinaryField()
