from tortoise import fields
from tortoise.models import Model


class Task(Model):
    id = fields.IntField(pk=True)
    datetime = fields.DatetimeField()
    callback = fields.BinaryField()
