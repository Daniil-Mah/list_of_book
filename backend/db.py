from peewee import MySQLDatabase

# Настройте данные для подключения под себя
db = MySQLDatabase("list_of_book_db",
    user="youruser",
    password="yourpassword",
    host="localhost",
    port=3306)
