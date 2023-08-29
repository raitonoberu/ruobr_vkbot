from os import getenv
from datetime import datetime

POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")

VK_TOKEN = getenv("VK_TOKEN")
VK_ID = getenv("VK_ID")  # ID группы с ботом

WAIT_IN_MINS = int(getenv("WAIT_IN_MINS")) or 20  # таймер обновления оценок
TIMEZONE = getenv("TIMEZONE") or "Asia/Novokuznetsk"  # часовой пояс
