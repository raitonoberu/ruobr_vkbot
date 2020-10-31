from os import getenv
from datetime import datetime

DATABASE_URL = getenv("DATABASE_URL")  # PostgreSQL URL
TOKEN = getenv("VK_TOKEN")
ID = getenv("VK_ID")  # ID группы с ботом
WAIT_IN_MINS = getenv("WAIT_IN_MINS") or 20  # таймер обновления оценок
TIMEZONE = getenv("TIMEZONE") or "Asia/Novokuznetsk"  # часовой пояс

# DEBUG
FORCE_DATE = getenv("FORCE_DATE")  # 2020-06-02
if FORCE_DATE:
    FORCE_DATE = datetime.fromisoformat(FORCE_DATE)
