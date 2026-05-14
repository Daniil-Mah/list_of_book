from peewee import MySQLDatabase

# Настройте данные для подключения под себя
db = MySQLDatabase(
    "books_db",       # имя вашей базы
    user="youruser",
    password="yourpassword",
    host="localhost",
    port=3306
)
