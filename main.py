import logging

logging.basicConfig(level=logging.INFO)

from vkbottle.bot import Bot, Message, MessageEvent
from vkbottle import GroupEventType
from db_access import Database
from notifier import Notifier
from datetime import datetime, timedelta
from time import time
import pytz
from config import POSTGRES_USER, POSTGRES_PASSWORD, VK_TOKEN, TIMEZONE
from utils import (
    food_to_str,
    marks_to_str,
    controlmarks_to_str,
    homework_to_str,
    progress_to_str,
    monday,
    mail_to_str,
)
import asyncio
import api as ruobr_api
import strings
import keyboards

db = Database(POSTGRES_USER, POSTGRES_PASSWORD)
tz = pytz.timezone(TIMEZONE)

bot = Bot(token=VK_TOKEN)


def equals_filter(words: list[str]):
    def func(m: Message):
        text = m.text.lower()
        return any(word == text for word in words)

    return func


def startswith_filter(words: list[str]):
    def func(m: Message):
        text = m.text.lower()
        return any(text.startswith(word) for word in words)

    return func


@bot.on.message(func=startswith_filter(strings.LOGIN))
async def login(message: Message):
    text = message.text
    vk_id = message.peer_id

    # проверка правильности данных для входа
    args = text.split(" ")
    if not (args[0].lower() in strings.LOGIN):
        return
    user = await db.get_user(vk_id)
    if user:  # пользователь существует
        await answer(message, f"Вы уже вошли как {user.name}.")
        return
    loginpassword = " ".join(args[1:])
    if not (":" in loginpassword):  # неправильная форма
        await answer(message, f'Пример: "{strings.LOGIN[0]} логин:пароль"')
        return
    loginpassword = loginpassword.split(":")
    if len(loginpassword) == 2:
        login, password = loginpassword
        child = None
    else:
        await answer(message, f'Пример: "{strings.LOGIN[0]} логин:пароль"')
        return

    # авторизация
    ruobr = ruobr_api.AsyncRuobr(login, password)
    try:
        children = await ruobr.get_children()
    except ruobr_api.AuthenticationException:
        await answer(message, "Проверьте логин и/или пароль.")
        return
    except:
        logging.exception("")
        await answer(message, "Произошла ошибка. Сообщите разработчику.")
        return

    # обработка родительского аккаунта
    if len(children) > 1:
        text = "На аккаунте обнаружено несколько детей:\n"
        i = 0
        for child in children:
            i += 1
            text += f'\n{i}. {child.get("first_name")} {child.get("last_name")} {child["group"]}'
        await answer(
            message, text, keyboard=keyboards.children_kb(login, password, children)
        )
        return
    else:  # один ребёнок
        user = children[0]

    name = user["first_name"] + " " + user["last_name"]
    await db.add_user(vk_id, login, password, name, user["id"])
    logging.info(str(vk_id) + " logged in")
    await answer(message, f"Вы вошли как {name}.", keyboards.MAIN)


@bot.on.message(func=equals_filter(strings.SUBSCRIBE))
async def subscribe(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
        return
    if not user.status:  # пользователь не подписан
        await db.update_status(vk_id, True)
        logging.info(str(vk_id) + " subscribed")
        await answer(message, "Вы подписались на обновления оценок.")
    else:
        await answer(message, "Вы уже подписаны.")


@bot.on.message(func=equals_filter(strings.UNSUBSCRIBE))
async def unsubscribe(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
        return
    if user.status:  # пользователь подписан
        await db.update_status(vk_id, False)
        await db.update_marks(vk_id, None)
        logging.info(str(vk_id) + " unsubscribed")
        await answer(message, "Вы отписались от обновлений оценок.")
    else:
        await answer(message, "Вы не подписаны.")


@bot.on.message(func=equals_filter(strings.LOGOUT))
async def logout(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
        return
    await db.remove_user(vk_id)
    logging.info(str(vk_id) + " logged out")
    await answer(message, "Вы вышли.")


@bot.on.message(func=equals_filter(strings.MARKS))
async def marks(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested marks")
    date0 = monday(datetime.now(tz))
    date1 = date0 + timedelta(days=6)
    try:
        marks = await ruobr_api.get_marks(user, date0, date1)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    await answer(
        message,
        marks_to_str(marks, date0, date1),
        keyboard=keyboards.marks_kb(user, date0, date1),
    )


@bot.on.message(func=equals_filter(strings.CONTROLMARKS))
async def controlmarks(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested controlmarks")
    try:
        controlmarks = await ruobr_api.get_controlmarks(user)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if controlmarks:
        await answer(message, controlmarks_to_str(controlmarks))
    else:
        await answer(message, "У Вас нет итоговых оценок за текущий период.")


@bot.on.message(func=equals_filter(strings.PROGRESS))
async def progress(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested progress")
    try:
        progress = await ruobr_api.get_progress(user)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if progress:
        await answer(message, progress_to_str(progress))
    else:
        await answer(message, "У Вас нет оценок за текущий период.")


@bot.on.message(func=equals_filter(strings.HOMEWORK))
async def homework(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested homework")
    date = datetime.now(tz)
    try:
        homework = await ruobr_api.get_homework(user, date, date + timedelta(days=14))
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if homework:
        await answer(message, "Домашние задания:\n" + homework_to_str(homework))
    else:
        await answer(message, "На ближайшие 2 недели ничего не задано.")


@bot.on.message(func=equals_filter(strings.FOOD))
async def food(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested food")
    date = datetime.now(tz)
    try:
        food = await ruobr_api.get_food(user, date)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if not food:
        await answer(message, "Нет информации о питании.")
        return
    await answer(message, food_to_str(food))


@bot.on.message(func=equals_filter(strings.MAIL))
async def mail(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested mail")
    try:
        letter = await ruobr_api.get_mail(user, 0)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if not letter:
        await answer(message, "Нет сообщений.")
        return
    await answer(message, mail_to_str(letter), keyboard=keyboards.mail_kb(user, 0))


@bot.on.message(func=equals_filter(strings.STATUS))
async def status(message: Message):
    vk_id = message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(message, "Вы не вошли.")
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

    await answer(message, result)


@bot.on.message(func=equals_filter(strings.COMMANDS))
async def commands(message: Message):
    await answer(message, strings.COMMANDS_TEXT, keyboard=keyboards.MAIN)


# KEYBOARDS


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def cb_keyboard(event: MessageEvent):
    payload = event.get_payload_json()
    if "payload" in payload:  # keyboards that don't work on PC
        return

    vk_id = event.peer_id
    user = await db.get_user(vk_id)

    if payload.get("type") == "children":
        if user:
            await event.show_snackbar("Вы уже вошли")
            return

        if time() - payload["time"] > 60:
            await event.show_snackbar("Время ожидания истекло")
            return

        ruobr = ruobr_api.AsyncRuobr(payload["login"], payload["password"])
        children = await ruobr.get_children()
        for user in children:
            if user["id"] == payload["id"]:
                break
        name = user["first_name"] + " " + user["last_name"]
        await db.add_user(
            vk_id, payload["login"], payload["password"], name, user["id"]
        )
        await event.show_snackbar("Вы вошли")
        logging.info(str(vk_id) + " logged in")
        return

    if (
        not user
        or user.ruobr_id != payload.get("id")
        or time() - payload.get("time") > 60 * 10
    ):
        return

    if payload.get("type") == "marks":
        date0 = (
            datetime.fromisoformat(payload["date0"])
            + timedelta(days=7) * payload["direction"]
        )

        date1 = (
            datetime.fromisoformat(payload["date1"])
            + timedelta(days=7) * payload["direction"]
        )
        try:
            marks = await ruobr_api.get_marks(user, date0, date1)
        except ruobr_api.AuthenticationException:
            await db.remove_user(user.vk_id)
            return

        await event.edit_message(
            marks_to_str(marks, date0, date1),
            keyboard=keyboards.marks_kb(user, date0, date1),
        )

    if payload.get("type") == "mail":
        index = payload["index"] + payload["direction"]
        if index < 0:
            return await empty_callback(event)

        try:
            mail = await ruobr_api.get_mail(user, index)
        except ruobr_api.AuthenticationException:
            await db.remove_user(user.vk_id)
            return

        if not mail:
            return await empty_callback(event)

        await event.edit_message(
            mail_to_str(mail),
            keyboard=keyboards.mail_kb(user, index),
        )


async def answer(message: Message, text, keyboard=None):
    if len(text) > 4096:
        await message.answer(text[:4096], dont_parse_links=True, keyboard=keyboard)
        await answer(message, text[4096:], keyboard=keyboard)
    else:
        await message.answer(text, dont_parse_links=True, keyboard=keyboard)


async def empty_callback(event: MessageEvent):
    data = {
        "event_id": event.event_id,
        "user_id": event.user_id,
        "peer_id": event.peer_id,
    }
    await bot.api.request("messages.sendMessageEventAnswer", data)


async def main():
    await db.connect()
    if not (await db.is_exists()):
        logging.info("Creating a new table...")
        await db.create_table()
    else:
        logging.info("Table already exists")
    notifier = Notifier(bot.api, db)
    notifier.run()
    await bot.run_polling()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    finally:
        logging.info("Closing database...")
        loop.run_until_complete(db.close())
