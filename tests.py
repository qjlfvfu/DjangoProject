# from django.test import TestCase

# Create your tests here.
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = psycopg2.connect(
        dbname=os.getenv("DATABASES_NAME"),
        user=os.getenv("DATABASES_USER"),
        password=os.getenv("DATABASES_PASSWORD"),
        host=os.getenv("DATABASES_HOST"),
        port=os.getenv("DATABASES_PORT"),
    )
    print("✅ Подключение к базе данных успешно!")

    # Проверяем версию
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"📌 {version[0]}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Ошибка: {e}")
