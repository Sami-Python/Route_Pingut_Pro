import json
import datetime
import pytz

def _get_localized_time(time_str: str):
    helsinki_tz = pytz.timezone('Europe/Helsinki')
    if '.' in time_str:
        time_str = time_str.split('.')[0] + '.' + time_str.split('.')[1][:6]
        return helsinki_tz.localize(datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f'))
    return helsinki_tz.localize(datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S'))

def get_events_from_outlook(calendar:json):
    events = []
    for event in calendar['value']:
        events.append({
            "title": event['subject'],
            "start": _get_localized_time(event['start']['dateTime']).strftime('%Y-%m-%dT%H:%M:%S'),
            "end": _get_localized_time(event['end']['dateTime']).strftime('%Y-%m-%dT%H:%M:%S'),
            "location": event['location']['displayName']
        })
    return events


if __name__ == "__main__":
    with open("./response_1764094006062.json", 'r') as f:
        data = json.load(f)
    events = get_events_from_outlook(data)
    for event in events:
        print(event)
    