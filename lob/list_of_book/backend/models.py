from peewee import *
from db import db

class BaseTable(Model):
    class Meta:
        database = db

class Users(BaseTable):
    nickname = CharField()
    role_adm = BooleanField(default=False)
    password = CharField()

class Author(BaseTable):
    nickname = CharField()

class Books(BaseTable):
    title = CharField()
    author_id = IntegerField()
    link_of_book = CharField()
    reading_status = BooleanField(default=True)
    bookmark = CharField()
    tegs_id = IntegerField()