import os
from peewee import MySQLDatabase
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Настройка подключения к базе данных MySQL
db = MySQLDatabase(
    os.getenv('DB_NAME', 'list_of_book_db'),      # Название базы данных
    user=os.getenv('DB_USER', 'root'),             # Имя пользователя MySQL
    password=os.getenv('DB_PASSWORD', 'MySQL/13579'),         # Пароль MySQL
    host=os.getenv('DB_HOST', 'localhost'),        # Хост (обычно localhost)
    port=int(os.getenv('DB_PORT', 3306))          # Порт MySQL по умолчанию
)
