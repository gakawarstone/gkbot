from tortoise import fields
from tortoise.models import Model


class Reminds(Model):
    user_id = fields.IntField(pk=True)
