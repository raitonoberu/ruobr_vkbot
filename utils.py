from datetime import datetime, timedelta
import re
from collections import defaultdict


def monday(date):
    while date.weekday() != 0:
        date -= timedelta(days=1)
    return date


def iso_to_string(iso_date):
    date = datetime.fromisoformat(iso_date)
    if date.hour:
        return date.strftime("%d %b %Y %H:%M")
    else:
        return date.strftime("%d %b %Y")


def convert_marks(timetable):
    marks = defaultdict(list)
    for lesson in timetable:
        if "marks" in lesson:
            for mark in lesson["marks"]:
                marks[lesson["subject"]].append(mark["mark"])
    # [{'Иностранный язык': ['5'], 'ОБЖ': ['4']}]
    return marks


def compare_marks(marks0, marks1):
    if marks0 == marks1:
        return {}
    result = marks1.copy()
    for subject, marks in marks0.items():
        try:
            if marks == marks1[subject]:
                result.pop(subject)
                continue
            for index, mark in enumerate(marks):
                if marks1[subject][index] == mark:
                    result[subject].pop(index)
        except (KeyError, IndexError):
            pass
    return result


def marks_to_str(marks, date0=None, date1=None):
    if date0 is not None:
        header = f"{date0.strftime('%d.%m')} -- {date1.strftime('%d.%m')}\n"
    else:
        header = ""
    if marks:
        marks = "\n".join(
            [
                f"• {subject.strip()}: {', '.join(marks)}"
                for subject, marks in marks.items()
            ]
        )
    else:
        marks = "Нет оценок за этот период."
    return header + marks


def convert_controlmarks(controlmarks):
    period = None
    for p in controlmarks:
        if p["marks_future"] == 0:
            period = p
            break
    return period


def controlmarks_to_str(period):
    return (
        period["title"]
        + "\n\n"
        + "\n".join([f"• {m['subject_name']}: {m['mark']}" for m in period["marks"]])
    )


def convert_homework(timetable):
    result = []
    for lesson in timetable:
        if "task" not in lesson:
            continue
        for task in lesson["task"]:
            result.append(
                {
                    "title": task["title"].strip(),
                    "subject": lesson["subject"].strip(),
                    "date": iso_to_string(task["deadline"]),
                    # "url": Ruobr.getHomeworkById(item["task"]["id"]),
                }
            )
    # [{'title': 'Task_title', 'subject': 'Subject', 'date': '2020-04-24'}...]
    return result


def homework_to_str(homework):
    return "\n\n".join(
        [f"• {item['subject']} ({item['date']}):\n{item['title']}" for item in homework]
    )


def convert_food(food, date: datetime):
    balance = food["balance"]
    complex = None
    dishes = None
    state = None

    if food["vizit"]:
        day = None
        date_str = date.strftime("%Y-%m-%d")
        for d in food["vizit"]:
            if d["date"] == date_str:
                day = d
                break
        if day:
            if "ordered_complex" in day:
                complex = day["ordered_complex"]
            elif "complex" in day:
                complex = day["complex"]

            if len(day["dishes"]) != 0:
                dishes = "\n".join(["• " + d["text"] for d in day["dishes"]])
            elif len(day["qs_unit"]) != 0:
                dishes = "\n".join([q["about"] for q in day["qs_unit"]])

            if "state_str" in day:
                state = day["state_str"]

    return {
        "balance": balance,
        "complex": complex,
        "dishes": dishes,
        "state": state,
    }


def food_to_str(food):
    answer = "Ваш баланс: " + food["balance"] + " руб.\n"
    if food["complex"] != None:
        answer += "На сегодня заказано: " + food["complex"]
        if food["dishes"]:
            answer += "\n\n" + food["dishes"]
        if food["state"]:
            answer += "\n\nСтатус: " + food["state"]
    else:
        answer += "На сегодня ничего не заказано."
    return answer


def convert_mail(_mail, index):
    mail = []
    for i in _mail:
        if i["author_id"] not in (-1, 1):
            # убрать эти надоедливые "ВНИМАНИЕ! Не прыгай под колёса!"
            mail.append(i)

    if index < len(mail):
        letter = mail[index]

        if letter["type_id"] != 2:
            key = "last_msg_text" if "last_msg_text" in letter else "clean_text"
            text = letter[key].replace("&nbsp;", " ")
        else:
            # убрать html теги
            text = re.sub(r"<[^>]*>", "", letter["last_msg_text"])
        return {
            "index": index,
            "count": len(mail),
            "date": letter["post_date"],
            "subject": letter["subject"],
            "author": letter["author"],
            "text": text,
        }


def mail_to_str(letter):
    return f"{letter['index'] + 1}/{letter['count']}\nДата: {iso_to_string(letter['date'])}\nТема: {letter['subject']}\nАвтор: {letter['author']}\n\n{letter['text']}"


def convert_progress(controlmarks):
    period = None
    for p in controlmarks:
        if p["marks_future"] == 1:
            period = p
            break
    return period


def progress_to_str(period):
    # посчитаем средний балл
    cnt = 0
    sm = 0
    for m in period["marks"]:
        if m["mark"] != 0.0:
            cnt += 1
            sm += m["mark"]
    avg = round(sm / cnt, 2) if cnt != 0 else 0

    return f"{period['title']}\nСредний балл: {avg}\n\n" + "\n".join(
        [
            f"• {item['subject_name'].strip()}: {item['mark']}"
            for item in period["marks"]
            if item["mark"] != 0.0
        ]
    )
