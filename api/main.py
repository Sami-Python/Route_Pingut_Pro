from fastapi import FastAPI
from fastapi.responses import FileResponse
import os
from graph_api import app as graph_app
from ical_api import app as ical_app
from weather_api import app as weather_app
from logger import setup_logging

# Initialize logging (captures prints and writes to api.log)
setup_logging()

app = FastAPI(title="API Gateway", version="1.0.0")
    
# Mount the existing APIs to specific paths
app.mount("/graph", graph_app)
app.mount("/ical", ical_app)
app.mount("/weather", weather_app)


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
            "weather_api": {
                "path": "/weather",
                "description": "Weather forecast for cities and routes"
            },
            "logs": {
                "path": "/logs",
                "description": "API logs"
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
