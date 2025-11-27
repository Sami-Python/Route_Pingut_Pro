from fastapi import FastAPI
from fastapi.responses import FileResponse
import os
from graph_api import app as graph_app
from cal_api import app as cal_app
from logger import setup_logging

# Initialize logging (captures prints and writes to api.log)
setup_logging()

app = FastAPI()
    
# Mount the existing APIs to specific paths
# You can access the graph API at /graph/...
# You can access the calendar API at /cal/...
app.mount("/graph", graph_app)
app.mount("/cal", cal_app)

@app.get("/")
async def root():
    return {
        "message": "Main API Gateway",
        "routes": {
            "graph_api": "/graph",
            "cal_api": "/cal",
            "logs": "/logs"
        }
    }

@app.get("/logs")
async def get_logs():
    log_file = "api.log"
    if os.path.exists(log_file):
        return FileResponse(log_file, media_type="text/plain")
    return {"error": "Log file not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
