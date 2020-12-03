from ruobr_api import *
from utils import convert_marks, convert_homework, convert_food
import logging
from httpx import ConnectTimeout
import asyncio


class AsyncRuobr(AsyncRuobr):
    async def _get(self, target):
        while True:
            try:
                return await super()._get(target)
            except ConnectTimeout as e:
                logging.info("timeout, trying again")


async def get_marks(user, date1, date2):
    ruobr = AsyncRuobr(user.username, user.password)
    ruobr.user = {"id": user.ruobr_id}
    marks = await ruobr.getMarks(date1, date2)
    return convert_marks(marks)


async def get_progress(user, date):
    ruobr = AsyncRuobr(user.username, user.password)
    ruobr.user = {"id": user.ruobr_id}
    progress = await ruobr.getProgress(date)
    return progress


async def get_homework(user, date1, date2):
    ruobr = AsyncRuobr(user.username, user.password)
    ruobr.user = {"id": user.ruobr_id}
    homework = await ruobr.getHomework(date1, date2)
    return convert_homework(homework)


async def get_food(user, date1, date2):
    ruobr = AsyncRuobr(user.username, user.password)
    ruobr.user = {"id": user.ruobr_id}
    info, history = await asyncio.gather(
        ruobr.getFoodInfo(), ruobr.getFoodHistory(date1, date2)
    )
    return convert_food(info, history)


async def get_mail(user):
    ruobr = AsyncRuobr(user.username, user.password)
    mail = await ruobr.getMail()
    if not mail:
        return {}
    letter = None
    for i in mail:  # search for unread letter
        if not i["read"]:
            letter = i
            await ruobr.readMessage(letter["id"])
            break
    if not letter:
        for i in mail:  # search for right letter
            if i["id"] != -1:
                letter = i
                break
    if not letter:  # no right letter
        return {}

    letter["clean_text"] = letter["clean_text"].replace("&nbsp;", "")
    return letter


async def get_news(user):
    ruobr = AsyncRuobr(user.username, user.password)
    news = await ruobr.getNews()
    if not news:
        return {}
    new = news[0]
    new["clean_text"] = new["clean_text"].replace("&nbsp;", "")
    return new


async def get_status(user):
    ruobr = AsyncRuobr(user.username, user.password)
    children = await ruobr.getChildren()
    for child in children:
        if child["id"] == user.ruobr_id:
            return child
