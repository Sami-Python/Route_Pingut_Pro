import json
import datetime
import pytz

def _get_localized_time(time_str: str):
    """
    Get the localized time from a string.
    """
    helsinki_tz = pytz.timezone('Europe/Helsinki')
    if '.' in time_str:
        time_str = time_str.split('.')[0] + '.' + time_str.split('.')[1][:6]
        return helsinki_tz.localize(datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f'))
    return helsinki_tz.localize(datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S'))

def get_events_from_outlook(calendar:json):
    """
    Get events from an Outlook calendar
    Returns a list of events as a list of dictionaries. 
    Each dictionary contains the event title, start time, end time, and location.
    """
    events = []
    for event in calendar['value']:
        events.append({
            "title": event['subject'],
            "start": _get_localized_time(event['start']['dateTime']).strftime('%Y-%m-%dT%H:%M:%S'),
            "end": _get_localized_time(event['end']['dateTime']).strftime('%Y-%m-%dT%H:%M:%S'),
            "location": event['location']['displayName']
        })
    return events