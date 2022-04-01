import json
from datetime import date


def events_for_today(all_events):
    data = json.loads(all_events)
    events = []
    result = ""

    today = date.today()

    for item in data['models']['listing']['fullData']:
        if item['date'] == str(today):
            events.append(item)

    for item in events:
        result = result + f"""Сегодня вы записаны на {item['groupName']} в {item['startTime']}. Преподаватель:  
                        {item['teacherName']}. {item['roomName']}\n\n"""
    if result == '':
        return f"Сегодня вы не записаны"
    else:
        return result
