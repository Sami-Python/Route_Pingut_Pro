import json
import datetime
import pytz

def _get_localized_time(time_str: str):
    """
    Get the localized time from a string.
    Handles ISO 8601 strings with or without timezone offsets.
    """
    helsinki_tz = pytz.timezone('Europe/Helsinki')
    
    # Handle 'Z' suffix for UTC, as fromisoformat only supports it in Python 3.11+
    if time_str.endswith('Z'):
        time_str = time_str[:-1] + '+00:00'
        
    try:
        dt = datetime.datetime.fromisoformat(time_str)
    except ValueError:
        # Handle cases like 7-digit microseconds (Outlook format)
        if '.' in time_str:
             base, fraction = time_str.split('.', 1)
             # Handle Z or offset in fraction
             if '+' in fraction:
                 frac_part, offset = fraction.split('+', 1)
                 offset = '+' + offset
             elif '-' in fraction:
                 # Need to be careful not to split negative year, but this is fraction part
                 # Assuming ISO8601 offset separator
                 parts = fraction.split('-')
                 # Last part is likely offset hour if time part is reasonable length
                 if len(parts) > 1:
                     frac_part = parts[0]
                     offset = '-' + '-'.join(parts[1:])
                 else:
                     frac_part = fraction
                     offset = ''
             elif 'Z' in fraction: # Should be handled by top check but good for robustness
                 frac_part = fraction.replace('Z', '')
                 offset = '+00:00'
             else:
                 frac_part = fraction
                 offset = ''
            
             if len(frac_part) > 6:
                 frac_part = frac_part[:6]
                 time_str = f"{base}.{frac_part}{offset}"
                 dt = datetime.datetime.fromisoformat(time_str)
             else:
                 raise
        else:
             raise

    if dt.tzinfo is not None:
        return dt.astimezone(helsinki_tz)
    
    return helsinki_tz.localize(dt)

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

def get_events_from_gcal(events: list):
    """
    Get events from a Google Calendar
    Returns a list of events as a list of dictionaries. 
    Each dictionary contains the event title, start time, end time, and location.
    """
    parsed_events = []
    for event in events:
        # Handle start time
        if 'dateTime' in event['start']:
            start = _get_localized_time(event['start']['dateTime']).strftime('%Y-%m-%dT%H:%M:%S')
        elif 'date' in event['start']:
            start = event['start']['date']
        else:
            continue # Skip events with no valid start time

        # Handle end time
        if 'dateTime' in event['end']:
            end = _get_localized_time(event['end']['dateTime']).strftime('%Y-%m-%dT%H:%M:%S')
        elif 'date' in event['end']:
            end = event['end']['date']
        else:
             # Fallback if end time is missing (though unusual for valid events)
             end = start

        parsed_events.append({
            "title": event.get('summary', 'No Title'),
            "start": start,
            "end": end,
            "location": event.get('location', '')
        })
    return parsed_events