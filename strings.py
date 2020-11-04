# команды
LOGIN = ("войти", "вход", "привет")
LOGOUT = ("выйти", "выход", "пока")
SUBSCRIBE = ("подписаться", "подписка")
UNSUBSCRIBE = ("отписаться", "отписка")
MARKS = ("оценки",)
HOMEWORK = ("дз", "домашнее задание", "домашние задания")
FOOD = ("питание", "еда")
MAIL = ("почта", "письма", "сообщения", "уведомления")
NEWS = ("новости",)
STATUS = ("статус",)
COMMANDS = ("команды", "помощь")

# текст списка команд
COMMANDS_TEXT = f"""Список команд:
• {LOGIN[0]} — войти в аккаунт (пример: "{LOGIN[0]} логин:пароль")
• {LOGOUT[0]} — выйти из аккаунта
• {SUBSCRIBE[0]} — подписаться на обновления оценок
• {UNSUBSCRIBE[0]} — отписаться от обновлений оценок
• {MARKS[0]} — получить оценки за неделю
• {HOMEWORK[0]} — получить домашние задания
• {FOOD[0]} — получить информацию о счёте питания
• {MAIL[0]} — получить последнее непрочитанное письмо
• {NEWS[0]} — получить последнюю новость
• {STATUS[0]} — получить информацию о текущем пользователе
• {COMMANDS[0]} — получить список команд"""
