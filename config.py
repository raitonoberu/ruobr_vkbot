from os import getenv

DATABASE_FILE = "users.db"
TOKEN = getenv("VK_TOKEN")
ID = getenv("VK_ID")  # ID группы с ботом
WAIT_IN_MINS = 20 or getenv("WAIT_IN_MINS")  # таймер обновления оценок
TIMEZONE = "Asia/Novokuznetsk" or getenv("TIMEZONE")  # часовой пояс
