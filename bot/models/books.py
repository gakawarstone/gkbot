from tortoise import fields
from tortoise.models import Model


class Book(Model):
    name = fields.TextField()
    author = fields.TextField()
    chapters_cnt = fields.IntField()
    current_chapter = fields.IntField(default=0)
    user_id = fields.IntField()
