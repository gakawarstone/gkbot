from tortoise import fields
from tortoise.models import Model


class GkFeed(Model):
    user_id = fields.IntField(pk=True)
    login = fields.TextField()
    password = fields.TextField()

    class Meta(Model.Meta):
        table = "gkfeed"
