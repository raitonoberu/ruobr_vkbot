from vkwave.bots import SimpleLongPollBot
from db_access import Database
from notifier import Notifier
from datetime import datetime, timedelta
import pytz
from config import DATABASE_URL, TOKEN, ID, TIMEZONE
from utils import marks_to_str, monday
import asyncio
import api as ruobr_api
import strings
import logging

logging.basicConfig(level=logging.INFO)

db = Database(DATABASE_URL)
tz = pytz.timezone(TIMEZONE)

bot = SimpleLongPollBot(tokens=TOKEN, group_id=ID)


@bot.message_handler(bot.text_contains_filter(strings.LOGIN))
async def login(event: bot.SimpleBotEvent):
    text = event.object.object.message.text
    vk_id = event.object.object.message.peer_id

    args = text.split(" ")
    if not (args[0].lower() == "войти"):
        return
    user = await db.get_user(vk_id)
    if user:  # пользователь существует
        await answer(event, f"Вы уже вошли как {user.name}.")
        return
    loginpassword = " ".join(args[1:])
    if not (":" in loginpassword):  # неправильная форма
        await answer(event, 'Пример: "войти <логин>:<пароль>"')
        return
    loginpassword = loginpassword.split(":")
    login = loginpassword[0]
    password = loginpassword[1]
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
    await answer(event, f"Вы вошли как {name}.")


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
    date = monday(datetime.now(tz))
    try:
        marks = await ruobr_api.get_marks(user, date, date + timedelta(days=6))
    except ruobr_api.AuthenticationException:
        db.remove_user(user.vk_id)
        return
    if marks:
        await answer(event, "Ваши оценки за неделю:\n" + marks_to_str(marks))
    else:
        await answer(event, "Вы не получали оценок за эту неделю.")


@bot.message_handler(bot.text_filter(strings.FOOD))
async def food(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    ruobr = ruobr_api.AsyncRuobr(user.username, user.password)
    ruobr.user = {"id": user.ruobr_id}
    try:
        info = await ruobr.getFoodInfo()
    except ruobr_api.AuthenticationException:
        db.remove_user(user.vk_id)
        return
    balance = round(int(info["balance"]) / 100, 1)
    date = datetime.now(tz)
    history = await ruobr.getFoodHistory(date, date)
    ordered = (
        f"На сегодня заказано: {history[0]['complex__name']}\nСтатус заказа: {history[0]['state_str']}"
        if history
        else "На сегодня ничего не заказано."
    )
    await answer(event, f"Ваш баланс: {balance} руб.\n{ordered}")


@bot.message_handler(bot.text_filter(strings.MAIL))
async def mail(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    ruobr = ruobr_api.AsyncRuobr(user.username, user.password)
    ruobr.user = {"id": user.ruobr_id}
    try:
        mail = await ruobr.getMail()
    except ruobr_api.AuthenticationException:
        db.remove_user(user.vk_id)
        return
    if not mail:
        await answer(event, "Нет сообщений.")
    letter = mail[0]
    for i in mail:
        if not i["read"]:
            letter = i
            await ruobr.readMessage(letter["id"])
            break
    await answer(
        event,
        f"Последнее непрочитанное сообщение ({letter['post_date']}):\nТема: {letter['subject']}\nАвтор: {letter['author']}\n\n{letter['clean_text']}",
    )


@bot.message_handler(bot.text_filter(strings.COMMANDS))
async def commands(event: bot.SimpleBotEvent):
    await answer(event, strings.COMMANDS_TEXT)


async def answer(event, text):
    if len(text) > 4096:  # макс длина сообщения
        await answer(event, text[:4096])
        text = text[4096:]
    await event.answer(text)


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
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    try:
        loop.run_forever()
    finally:
        logging.info("Closing database...")
        loop.run_until_complete(db.close())
