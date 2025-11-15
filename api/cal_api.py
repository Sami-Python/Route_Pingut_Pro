from fastapi import FastAPI
from icalevents.icaldownload import ICalDownload
import icalendar
import pytz
from typing import Optional

app = FastAPI()

@app.get("/events")
async def get_calendar_events(url: str):
    downloader = ICalDownload()
    try:
        data = downloader.data_from_url(url)
    except Exception as e:
        return {"error": f"Failed to download calendar data from url: {url}", "details": str(e)}
        
    calendar = icalendar.Calendar.from_ical(data)

    calendar_events = []
    helsinki_tz = pytz.timezone('Europe/Helsinki')

    for event in calendar.walk('VEVENT'):
        start_dt = event.get('DTSTART').dt
        end_dt = event.get('DTEND').dt

        if start_dt.tzinfo is None:
            start_dt = helsinki_tz.localize(start_dt)
        else:
            start_dt = start_dt.astimezone(helsinki_tz)
        
        if end_dt.tzinfo is None:
            end_dt = helsinki_tz.localize(end_dt)
        else:
            end_dt = end_dt.astimezone(helsinki_tz)

        tmp = {
            "title": str(event.get('SUMMARY')),
            "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "description": str(event.get('DESCRIPTION', ''))
        }
        calendar_events.append(tmp)
    
    return calendar_events