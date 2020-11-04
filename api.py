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
    letter = mail[0]
    for i in mail:
        if not i["read"]:
            letter = i
            await ruobr.readMessage(letter["id"])
            break
    return letter


async def get_news(user):
    ruobr = AsyncRuobr(user.username, user.password)
    news = await ruobr.getNews()
    if not news:
        return {}
    return news[0]


async def get_status(user):
    ruobr = AsyncRuobr(user.username, user.password)
    status = await ruobr.getUser()
    return status
