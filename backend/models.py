from peewee import Model, CharField, IntegerField
from .db import db

class Book(Model):
    title = CharField()
    author = CharField()
    year = IntegerField()

    class Meta:
        database = db
