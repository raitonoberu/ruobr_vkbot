"""
TODO:
• Проверить работу нотифайера
• Обработать ситуацию, когда отправить сообщение невозможно
• Каким-то образом обработать родительский профиль
"""
from vkwave.bots import SimpleLongPollBot
from db_access import Database
from notifier import Notifier
from datetime import datetime, timedelta
import pytz
import locale
from config import DATABASE_URL, TOKEN, ID, TIMEZONE, FORCE_DATE
from utils import marks_to_str, homework_to_str, monday, iso_to_string
import asyncio
import api as ruobr_api
import strings
import keyboards
import logging

logging.basicConfig(level=logging.INFO)

db = Database(DATABASE_URL)
tz = pytz.timezone(TIMEZONE)
locale.setlocale(locale.LC_ALL, "ru_RU")

bot = SimpleLongPollBot(tokens=TOKEN, group_id=ID)


@bot.message_handler(bot.text_contains_filter(strings.LOGIN))
async def login(event: bot.SimpleBotEvent):
    text = event.object.object.message.text
    vk_id = event.object.object.message.peer_id

    args = text.split(" ")
    if not (args[0].lower() in strings.LOGIN):
        return
    user = await db.get_user(vk_id)
    if user:  # пользователь существует
        await answer(event, f"Вы уже вошли как {user.name}.")
        return
    loginpassword = " ".join(args[1:])
    if not (":" in loginpassword):  # неправильная форма
        await answer(event, f'Пример: "{strings.LOGIN[0]} логин:пароль"')
        return
    login, password = loginpassword.split(":")
    try:
        user = await ruobr_api.AsyncRuobr(login, password).getUser()
    except ruobr_api.AuthenticationException:
        await answer(event, "Проверьте логин и/или пароль.")
        return
    except:
        logging.exception("")
        await answer(event, "Произошла ошибка. Сообщите разработчику.")
        return
    name = user["first_name"] + " " + user["last_name"]
    await db.add_user(vk_id, login, password, name, user["id"])
    logging.info(str(vk_id) + " logged in")
    await answer(event, f"Вы вошли как {name}.", keyboards.MAIN)


@bot.message_handler(bot.text_filter(strings.SUBSCRIBE))
async def subscribe(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    if not user.status:  # пользователь не подписан
        await db.update_status(vk_id, True)
        logging.info(str(vk_id) + " subscribed")
        await answer(event, "Вы подписались на обновления оценок.")
    else:
        await answer(event, "Вы уже подписаны.")


@bot.message_handler(bot.text_filter(strings.UNSUBSCRIBE))
async def unsubscribe(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    if user.status:  # пользователь подписан
        await db.update_status(vk_id, False)
        logging.info(str(vk_id) + " unsubscribed")
        await answer(event, "Вы отписались от обновлений оценок.")
    else:
        await answer(event, "Вы не подписаны.")


@bot.message_handler(bot.text_filter(strings.LOGOUT))
async def logout(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    await db.remove_user(vk_id)
    logging.info(str(vk_id) + " logged out")
    await answer(event, "Вы вышли.")


@bot.message_handler(bot.text_filter(strings.MARKS))
async def marks(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested marks")
    date = FORCE_DATE if FORCE_DATE else monday(datetime.now(tz))
    try:
        marks = await ruobr_api.get_marks(user, date, date + timedelta(days=6))
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if marks:
        await answer(event, "Ваши оценки за неделю:\n" + marks_to_str(marks))
    else:
        await answer(event, "Вы не получали оценок за эту неделю.")


@bot.message_handler(bot.text_filter(strings.HOMEWORK))
async def homework(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested homework")
    date = FORCE_DATE if FORCE_DATE else datetime.now(tz)
    try:
        homework = await ruobr_api.get_homework(user, date, date + timedelta(days=14))
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if homework:
        await answer(event, "Домашние задания:\n" + homework_to_str(homework))
    else:
        await answer(event, "Ничего не задано.")


@bot.message_handler(bot.text_filter(strings.FOOD))
async def food(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested food")
    date = FORCE_DATE if FORCE_DATE else datetime.now(tz)
    try:
        food = await ruobr_api.get_food(user, date, date)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    ordered = (
        f"На сегодня заказано: {food['complex']}\nСтатус заказа: {food['state']}"
        if food["complex"]
        else "На сегодня ничего не заказано."
    )
    await answer(event, f"Ваш баланс: {food['balance']} руб.\n{ordered}")


@bot.message_handler(bot.text_filter(strings.MAIL))
async def mail(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested mail")
    try:
        letter = await ruobr_api.get_mail(user)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if not letter:
        await answer(event, "Нет сообщений.")
        return
    await answer(
        event,
        f"Последнее непрочитанное сообщение:\nДата: {iso_to_string(letter['post_date'])}\nТема: {letter['subject']}\nАвтор: {letter['author']}\n\n{letter['clean_text']}",
    )


@bot.message_handler(bot.text_filter(strings.NEWS))
async def news(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested news")
    try:
        new = await ruobr_api.get_news(user)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if not new:
        await answer(event, "Нет новостей.")
        return
    await answer(
        event,
        f"Последняя новость:\nЗаголовок: {new['title']}\nДата: {iso_to_string(new['date'])}\n\n{new['clean_text']}",
    )


@bot.message_handler(bot.text_filter(strings.STATUS))
async def status(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested status")
    try:
        status = await ruobr_api.get_status(user)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    name = " ".join(
        [
            status.get("last_name", ""),
            status.get("first_name", ""),
            status.get("middle_name", ""),
        ]
    )
    result = f"{name}\n\nID: {status['id']}\nШкола: {status['school']}\nКласс: {status['group']}\n\n"

    result += (
        "Вы подписаны на обновления оценок."
        if user.status
        else "Вы не подписаны на обновления оценок."
    )

    await answer(event, result)


@bot.message_handler(bot.text_filter(strings.COMMANDS))
async def commands(event: bot.SimpleBotEvent):
    await answer(event, strings.COMMANDS_TEXT)


async def answer(event, text, keyboard=None):
    if len(text) > 4096:
        await event.answer(text[:4096], dont_parse_links=True, keyboard=keyboard)
        await answer(event, text[4096:], keyboard=keyboard)
    else:
        await event.answer(text, dont_parse_links=True, keyboard=keyboard)


async def main():
    await db.connect()
    if not (await db.is_exists()):
        logging.info("Creating a new table...")
        await db.create_table()
    else:
        logging.info("Table already exists")
    notifier = Notifier(bot.api_context, db)
    notifier.run()
    await bot.run()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    finally:
        logging.info("Closing database...")
        loop.run_until_complete(db.close())
