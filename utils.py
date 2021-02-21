from datetime import datetime, timedelta
from ruobr_api import Ruobr


def convert_marks(marks):
    # {'Иностранный язык': [{'question_name': 'Ответ на уроке', 'question_id': 102494195, 'number': 1, 'question_type': 'Ответ на уроке', 'mark': '5'}], 'ОБЖ': [{'question_name': 'Ответ на уроке', 'question_id': 101356763, 'number': 1, 'question_type': 'Ответ на уроке', 'mark': '4'}]}
    marks = {key: [i["mark"] for i in marks[key]] for key in marks.keys()}
    return marks
    # [{'Иностранный язык': ['5'], 'ОБЖ': ['4']}]


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


def marks_to_str(marks, date0, date1):
    header = f"{date0.strftime('%d.%m')} -- {date1.strftime('%d.%m')}"
    if marks:
        marks = "\n".join(
            [
                f"{subject.strip()}: {', '.join(marks)}"
                for subject, marks in marks.items()
            ]
        )
    else:
        marks = "Нет оценок за этот период."
    return header + "\n\n" + marks


def controlmarks_to_str(controlmarks):
    # should I use [0] instead of [-1]?
    return f"{controlmarks[-1]['title']}\n\n{chr(10).join([f'• {subject}: {mark}' for subject, mark in controlmarks[-1]['marks'].items()])}"


def convert_homework(homework):
    # [{'task': {'title': 'Task_title', 'doc': False, 'requires_solutions': False, 'deadline': '2020-04-24', 'test_id': None, 'type': 'group', 'id': 99999999}, 'subject': 'Subject'}...]
    result = []
    for item in homework:
        result.append(
            {
                "title": item["task"]["title"],
                "subject": item["subject"].strip(),
                "date": iso_to_string(item["task"]["deadline"]),
                "url": Ruobr.getHomeworkById(item["task"]["id"]),
            }
        )
    return result
    # [{'title': 'Task_title', 'subject': 'Subject', 'date': '2020-04-24', 'url': 'http://url'}...]


def homework_to_str(homework):
    return "\n\n".join(
        [
            f"• {item['subject']} ({item['date']}):\n{item['title']}\nПодробнее: {item['url']}"
            for item in homework
        ]
    )


def convert_food(info, history):
    if history:
        complex = history[0]["complex__name"]
        state = history[0]["state_str"]
    else:
        complex = None
        state = None
    return {
        "balance": round(int(info["balance"]) / 100, 1),
        "complex": complex,
        "state": state,
    }


def subjects_to_str(subjects):
    # [{'place_count': 17, 'place': 3, 'group_avg': 3.69, 'child_avg': 4.29, 'parallels_avg': 3.56, 'subject': 'Русский язык'}, ...]
    return "\n".join(
        [f"• {item['subject'].strip()}: {item['child_avg']}" for item in subjects]
    )


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
