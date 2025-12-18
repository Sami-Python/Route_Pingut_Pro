from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
<<<<<<< HEAD
from dotenv import load_dotenv

load_dotenv()
from api.graph_api import app as graph_app
from api.ical_api import app as ical_app
from api.weather_api import app as weather_app
from api.gcal_api import app as gcal_app
from api.logger import setup_logging
from api.maps_api import app as maps_app
=======
from graph_api import app as graph_app
from ical_api import app as ical_app
from weather_api import app as weather_app
from gcal_api import app as gcal_app
from here_maps_api import app as here_maps_app
from logger import setup_logging
from maps_api import app as maps_app
>>>>>>> 2ac424f011da62b5d6990ac92ac08cca9b79f65f

# Initialize logging (captures prints and writes to api.log)
setup_logging()

app = FastAPI(title="API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



    
# Mount the existing APIs to specific paths
app.mount("/graph", graph_app)
app.mount("/ical", ical_app)
app.mount("/weather", weather_app)
app.mount("/gcal", gcal_app)
app.mount("/maps", maps_app)
app.mount("/here", here_maps_app)


@app.get("/")
async def root():
    """Root endpoint for the main API Gateway.
    
    Returns
    -------
    dict
        Available routes and their descriptions.
    """
    return {
        "message": "Main API Gateway",
        "routes": {
            "graph_api": {
                "path": "/graph",
                "description": "Microsoft Outlook calendar integration"
            },
            "ical_api": {
                "path": "/ical",
                "description": "Public iCal calendar integration"
            },
            "gcal_api": {
                "path": "/gcal",
                "description": "Google Calendar integration"
            },
            "weather_api": {
                "path": "/weather",
                "description": "Weather forecast for cities and routes"
            },
            "here_maps_api": {
                "path": "/here",
                "description": "HERE Maps routing and Digitraffic traffic"
            },
            "logs": {
                "path": "/logs",
                "description": "API logs"
            },
            "maps_api": {
                "path": "/maps",
                "description": "Maps API"
            }
        }
    }


@app.get("/logs")
async def get_logs():
    """Get the log file.
    
    Returns
    -------
    FileResponse or dict
        Log file or error message if not found.
    """
    log_file = "api.log"
    if os.path.exists(log_file):
        return FileResponse(log_file, media_type="text/plain")
    return {"error": "Log file not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

