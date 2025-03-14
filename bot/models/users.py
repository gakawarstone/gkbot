from tortoise import fields
from tortoise.models import Model


class Users(Model):
    user_id = fields.IntField(primary_key=True)
    user_name = fields.TextField()
