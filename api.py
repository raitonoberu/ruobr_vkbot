from ruobr_api import *
from utils import (
    convert_controlmarks,
    convert_marks,
    convert_homework,
    convert_food,
    convert_mail,
    convert_progress,
)
import logging
from httpx import ConnectTimeout


class AsyncRuobr(AsyncRuobr):
    async def _get(self, target):
        while True:
            try:
                return await super()._get(target)
            except ConnectTimeout:
                logging.info("timeout, trying again")


def get_ruobr(user):
    ruobr = AsyncRuobr(user.username, user.password)
    ruobr._children = [{"id": user.ruobr_id}]
    ruobr.is_authorized = True
    return ruobr


async def get_marks(user, date1, date2):
    ruobr = get_ruobr(user)
    timetable = await ruobr.get_timetable(date1, date2)
    return convert_marks(timetable)


async def get_controlmarks(user):
    ruobr = get_ruobr(user)
    controlmarks = await ruobr.get_control_marks()
    return convert_controlmarks(controlmarks)


async def get_progress(user):
    ruobr = get_ruobr(user)
    controlmarks = await ruobr.get_control_marks()
    return convert_progress(controlmarks)


async def get_homework(user, date1, date2):
    ruobr = get_ruobr(user)
    timetable = await ruobr.get_timetable(date1, date2)
    return convert_homework(timetable)


async def get_food(user, date):
    # здесь нам нужны доп параметры, получаем юзера
    ruobr = AsyncRuobr(user.username, user.password)
    index = 0
    children = await ruobr.get_children()
    for i in range(len(children)):
        if children[i]["id"] == user.ruobr_id:
            index = i
            break
    ruobr.child = index

    food = await ruobr.get_food_info(date)
    if not food:
        return None
    return convert_food(food, date)


async def get_mail(user, index):
    ruobr = get_ruobr(user)
    mail = await ruobr.get_mail()
    return convert_mail(mail, index)


async def get_status(user):
    ruobr = AsyncRuobr(user.username, user.password)
    children = await ruobr.get_children()
    for child in children:
        if child["id"] == user.ruobr_id:
            return child
