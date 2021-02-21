from vkwave.bots import SimpleLongPollBot
from vkwave.bots.utils.keyboards import keyboard
from db_access import Database
from notifier import Notifier
from datetime import datetime, timedelta
import json
from time import time
import pytz
import locale
from config import DATABASE_URL, TOKEN, ID, TIMEZONE, FORCE_DATE
from utils import (
    marks_to_str,
    controlmarks_to_str,
    homework_to_str,
    subjects_to_str,
    monday,
    iso_to_string,
)
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

    # проверка правильности данных для входа
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
    loginpassword = loginpassword.split(":")
    if len(loginpassword) == 2:
        login, password = loginpassword
        child = None
    else:
        await answer(event, f'Пример: "{strings.LOGIN[0]} логин:пароль"')
        return

    # авторизация
    ruobr = ruobr_api.AsyncRuobr(login, password)
    try:
        children = await ruobr.getChildren()
    except ruobr_api.AuthenticationException:
        await answer(event, "Проверьте логин и/или пароль.")
        return
    except:
        logging.exception("")
        await answer(event, "Произошла ошибка. Сообщите разработчику.")
        return

    # обработка родительского аккаунта
    if len(children) > 1:
        text = "На аккаунте обнаружено несколько детей:\n"
        i = 0
        for child in children:
            i += 1
            text += f'\n{i}. {child.get("first_name")} {child.get("last_name")} {child["group"]}'
        await answer(
            event, text, keyboard=keyboards.children_kb(login, password, children)
        )
        return
    else:  # один ребёнок
        user = children[0]

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
        await db.update_marks(vk_id, None)
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
    date0 = FORCE_DATE if FORCE_DATE else monday(datetime.now(tz))
    date1 = date0 + timedelta(days=6)
    try:
        marks = await ruobr_api.get_marks(user, date0, date1)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    await answer(
        event,
        marks_to_str(marks, date0, date1),
        keyboard=keyboards.marks_kb(user, date0, date1),
    )


@bot.message_handler(bot.text_filter(strings.CONTROLMARKS))
async def controlmarks(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested controlmarks")
    try:
        controlmarks = await ruobr_api.get_controlmarks(user)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if len(controlmarks) != 0:
        await answer(
            event,
            controlmarks_to_str(controlmarks),
        )
    else:
        await answer(event, "У Вас нет итоговых оценок за текущий период.")


@bot.message_handler(bot.text_filter(strings.PROGRESS))
async def progress(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    logging.info(str(vk_id) + " requested progress")
    date = FORCE_DATE if FORCE_DATE else datetime.now(tz)
    try:
        progress = await ruobr_api.get_progress(user, date)
    except ruobr_api.AuthenticationException:
        await db.remove_user(user.vk_id)
        return
    if progress:
        await answer(
            event,
            f"{progress['period_name']}\nСредний балл: {progress['child_avg']}\nМесто в классе: {progress['place']}\n\n{subjects_to_str(progress['subjects'])}",
        )
    else:
        await answer(event, "У Вас нет оценок за текущий период.")


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
    await answer(event, strings.COMMANDS_TEXT, keyboard=keyboards.MAIN)


# KEYBOARDS


@bot.message_handler(bot.payload_filter(None))
async def pl_keyboard(event: bot.SimpleBotEvent):
    # payload keyboard
    payload = json.loads(event.object.object.message.payload)
    if "payload" in payload:  # keyboards that don't work on PC
        return

    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)

    # children
    if payload.get("type") == "children":
        if user:
            await answer(event, "Вы уже вошли.")
            return

        if time() - payload["time"] > 60:
            await answer(event, "Время ожидания истекло.")
            return

        ruobr = ruobr_api.AsyncRuobr(payload["login"], payload["password"])
        children = await ruobr.getChildren()
        for user in children:
            if user["id"] == payload["id"]:
                break
        name = user["first_name"] + " " + user["last_name"]
        await db.add_user(
            vk_id, payload["login"], payload["password"], name, user["id"]
        )
        await answer(event, "Вы вошли.", keyboard=keyboards.MAIN)
        logging.info(str(vk_id) + " logged in")
        return


@bot.handler(bot.event_type_filter("message_event"))
async def cb_keyboard(event: bot.SimpleBotEvent):
    # callback keyboard
    payload = event.object.object.payload
    vk_id = event.object.object.peer_id
    user = await db.get_user(vk_id)

    if (
        not user
        or user.ruobr_id != int(payload.get("id"))
        or time() - float(payload.get("time")) > 60 * 10
    ):
        return

    # marks
    if payload.get("type") == "marks":
        date0 = datetime.fromisoformat(payload["date0"]) + timedelta(days=7) * int(
            payload["direction"]
        )
        date1 = datetime.fromisoformat(payload["date1"]) + timedelta(days=7) * int(
            payload["direction"]
        )
        try:
            marks = await ruobr_api.get_marks(user, date0, date1)
        except ruobr_api.AuthenticationException:
            await db.remove_user(user.vk_id)
            return

        await event.api_ctx.messages.edit(
            vk_id,
            message=marks_to_str(marks, date0, date1),
            conversation_message_id=event.object.object.conversation_message_id,
            keyboard=keyboards.marks_kb(user, date0, date1),
        )
        await event.callback_answer(None)


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
