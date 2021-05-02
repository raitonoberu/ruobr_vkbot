from ruobr_api import *
from utils import convert_marks, convert_homework, convert_food, convert_mail, convert_news
import logging
from httpx import ConnectTimeout
import asyncio


class AsyncRuobr(AsyncRuobr):
    def __init__(self, username, password):
        super().__init__(username, password, True)
        # TODO: use pydantic types

    async def _get(self, target):
        while True:
            try:
                return await super()._get(target)
            except ConnectTimeout:
                logging.info("timeout, trying again")


def get_ruobr(user):
    ruobr = AsyncRuobr(user.username, user.password)
    ruobr._children = [{"id": user.ruobr_id}]
    ruobr.isAuthorized = True
    return ruobr

async def get_marks(user, date1, date2):
    ruobr = get_ruobr(user)
    marks = await ruobr.getMarks(date1, date2)
    return convert_marks(marks)


async def get_controlmarks(user):
    ruobr = get_ruobr(user)
    controlmarks = await ruobr.getControlmarks()
    return controlmarks


async def get_progress(user, date):
    ruobr = get_ruobr(user)
    progress = await ruobr.getProgress(date)
    return progress


async def get_homework(user, date1, date2):
    ruobr = get_ruobr(user)
    homework = await ruobr.getHomework(date1, date2)
    return convert_homework(homework)


async def get_food(user, date1, date2):
    ruobr = get_ruobr(user)
    info, history = await asyncio.gather(
        ruobr.getFoodInfo(), ruobr.getFoodHistory(date1, date2)
    )
    return convert_food(info, history)


async def get_mail(user, index):
    ruobr = AsyncRuobr(user.username, user.password)
    mail = await ruobr.getMail()
    return convert_mail(mail, index)


async def get_news(user, index):
    ruobr = AsyncRuobr(user.username, user.password)
    news = await ruobr.getNews()
    return convert_news(news, index)


async def get_status(user):
    ruobr = AsyncRuobr(user.username, user.password)
    children = await ruobr.getChildren()
    for child in children:
        if child["id"] == user.ruobr_id:
            return child
