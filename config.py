from os import getenv

DATABASE_URL = getenv("DATABASE_URL")  # PostgreSQL URL
TOKEN = getenv("VK_TOKEN")
ID = getenv("VK_ID")  # ID группы с ботом
WAIT_IN_MINS = getenv("WAIT_IN_MINS") or 20  # таймер обновления оценок
TIMEZONE = getenv("TIMEZONE") or "Asia/Novokuznetsk"  # часовой пояс
