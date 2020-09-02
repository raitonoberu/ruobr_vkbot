"""
TODO:
- Возвращение дз
"""

from vkwave.bots import SimpleLongPollBot
from db_access import Database
from notifier import Notifier
from datetime import datetime, timedelta
import pytz
from config import DATABASE_FILE, TOKEN, ID, TIMEZONE
from help import convert_marks, marks_to_str, monday
import asyncio
import safe_api as ruobr_api
import logging

logging.basicConfig(level=logging.INFO)

db = Database(DATABASE_FILE)
tz = pytz.timezone(TIMEZONE)

bot = SimpleLongPollBot(tokens=TOKEN, group_id=ID)


@bot.message_handler(bot.text_contains_filter("войти"))
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
    except ruobr_api.AuthError:
        await answer(event, "Проверьте логин и/или пароль.")
        return
    except Exception as e:
        logging.error(e)
        await answer(event, "Произошла ошибка.")
        return
    name = user["first_name"] + " " + user["last_name"]
    await db.add_user(vk_id, login, password, name, user["id"])
    logging.info(str(vk_id) + " logged in")
    await answer(event, f"Вы успешно вошли как {name}.")


@bot.message_handler(bot.text_filter("подписаться"))
async def subscribe(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    if not user.status:  # пользователь не подписан
        await db.update_status(vk_id, True)
        logging.info(str(vk_id) + " subscribed")
        await answer(event, "Вы успешно подписались.")
    else:
        await answer(event, "Вы уже подписаны.")


@bot.message_handler(bot.text_filter("отписаться"))
async def unsubscribe(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    if user.status:  # пользователь подписан
        await db.update_status(vk_id, False)
        logging.info(str(vk_id) + " unsubscribed")
        await answer(event, "Вы успешно отписались.")
    else:
        await answer(event, "Вы не подписаны.")


@bot.message_handler(bot.text_filter("выйти"))
async def logout(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    await db.remove_user(vk_id)
    logging.info(str(vk_id) + " logged out")
    await answer(event, "Вы успешно вышли.")


@bot.message_handler(bot.text_filter("оценки"))
async def marks(event: bot.SimpleBotEvent):
    vk_id = event.object.object.message.peer_id
    user = await db.get_user(vk_id)
    if not user:
        await answer(event, "Вы не вошли.")
        return
    date = monday(datetime.now(tz))
    try:
        marks = await ruobr_api.get_marks(user, date, date + timedelta(days=6))
    except ruobr_api.AuthError:
        db.remove_user(user.vk_id)
        return
    if marks:
        await answer(
            event, "Ваши оценки за неделю:\n" + marks_to_str(convert_marks(marks))
        )
    else:
        await answer(event, "Вы не получали оценок за эту неделю.")


@bot.message_handler(bot.text_filter("питание"))
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
    except ruobr_api.AuthError:
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


@bot.message_handler(bot.text_filter("почта"))
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
    except ruobr_api.AuthError:
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


async def answer(event, text):
    if len(text) > 4096:  # макс длина сообщения
        await answer(event, text[:4096])
        text = text[4096:]
    await event.answer(text)


def main():
    notifier = Notifier(bot.api_context, db)
    notifier.run()
    bot.run_forever()


if __name__ == "__main__":
    main()
