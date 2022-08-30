from tortoise import fields
from tortoise.models import Model


class Users(Model):
    user_id = fields.IntField(pk=True)
    user_name = fields.TextField()
