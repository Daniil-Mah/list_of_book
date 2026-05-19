from peewee import *
from .db import db

# Базовый класс для всех моделей с поддержкой мягкого удаления
class BaseTable(Model):
    is_active = BooleanField(default=True)  # True - активна, False - удалена (скрыта)
    
    class Meta:
        database = db

# Модель пользователя
class Users(BaseTable):
    nickname = CharField(unique=True)        # Уникальный никнейм
    password = CharField()                    # Пароль
    role_adm = BooleanField(default=False)    # True - администратор, False - обычный пользователь

# Модель автора (привязана к конкретному пользователю)
class Author(BaseTable):
    nickname = CharField()                    # Имя автора
    user = ForeignKeyField(Users, backref='authors', on_delete='CASCADE')  # Владелец записи

# Модель книги (привязана к пользователю и автору)
class Books(BaseTable):
    title = CharField()                       # Название книги
    author = ForeignKeyField(Author, backref='books', on_delete='CASCADE')  # Связь с автором
    link_of_book = CharField()                # Ссылка на книгу
    reading_status = BooleanField(default=True)  # True - читается, False - прочитана
    bookmark = CharField(null=True)           # Закладка
    user = ForeignKeyField(Users, backref='books', on_delete='CASCADE')  # Владелец записи