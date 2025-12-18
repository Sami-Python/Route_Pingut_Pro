import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import msal
import requests
from dotenv import load_dotenv
import api.utils.cal_utils as cal_utils

# Load environment variables
load_dotenv()
# Initialize FastAPI app
app = FastAPI()

# Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTHORITY = os.getenv("AUTHORITY", "https://login.microsoftonline.com/consumers")
REDIRECT_PATH = os.getenv("REDIRECT_PATH", "/callback")
# Configuration for the Microsoft Graph API
SCOPE = ["User.Read", "Calendars.Read"]

# Build the MSAL app with the client ID, authority, and client secret   
def _build_msal_app(cache=None, authority=None):
    """
    Build the MSAL app with the client ID, authority, and client secret
    """
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=authority or AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache,
    )

# Get the authorization URL for the user to login
def _get_auth_url(redirect_uri: str):
    """
    Get the authorization URL for the user to login
    """
    print(f"Using Redirect URI: {redirect_uri}")
    print(f"SCOPE: {SCOPE}")
    msal_app = _build_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        SCOPE,
        redirect_uri=redirect_uri,
    )
    print(f"Auth URL: {auth_url}")
    return auth_url

# Get the access token from the authorization code
def _get_token_from_code(code: str, redirect_uri: str):
    """
    Get the access token from the authorization code
    """
    msal_app = _build_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPE,
        redirect_uri=redirect_uri,
    )
    return result


@app.get("/")
async def root():
    return {"message": "Welcome to the Outlook Calendar API. Go to /login to start."}

@app.get("/login")
async def login(request: Request):
    """
    Login endpoint for the authorization code flow.
    """
    # Construct the redirect URI based on the request's base URL
    # This handles http vs https and port numbers automatically
    if "http" in REDIRECT_PATH:
         redirect_uri = REDIRECT_PATH
    else:
         redirect_uri = str(request.url_for("callback"))
    print(f"Using Redirect URI: {redirect_uri}")
    # If running behind a proxy (like ngrok or docker), you need to force https or specific host
    auth_url = _get_auth_url(redirect_uri)
    print(auth_url)
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request, code: str):
    """
    Callback endpoint for the authorization code flow.
    """
    if "http" in REDIRECT_PATH:
         redirect_uri = REDIRECT_PATH
    else:
         redirect_uri = str(request.url_for("callback"))
    result = _get_token_from_code(code, redirect_uri)
    
    if "error" in result:
        return {"error": result.get("error"), "description": result.get("error_description")}
    
    # Redirect to Streamlit app with the token
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
    redirect_url = f"{frontend_url}?access_token={result.get('access_token')}"
    
    return RedirectResponse(url=redirect_url)


@app.get("/calendars")
async def get_calendars(token: str):
    """
    Get user's calendars from Outlook
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    graph_url = "https://graph.microsoft.com/v1.0/me/calendars"
    
    response = requests.get(graph_url, headers=headers)
    
    if response.status_code != 200:
        return {"error": "Failed to fetch calendars", "status": response.status_code, "details": response.json()}
    
    return response.json()



@app.get("/events")
async def get_events(token: str, calendar_id: Optional[str] = None):
    """
    Get events from an Outlook calendar
    Returns a list of events as a list of dictionaries. 
    Each dictionary contains the event title, start time, end time, and location.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Fetch events from the default calendar or specific calendar
    if calendar_id:
        graph_url = f"https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events"
    else:
        # https://graph.microsoft.com/v1.0/me/events
        graph_url = "https://graph.microsoft.com/v1.0/me/events"
    
    # You can add query parameters like $select, $top, etc.
    params = {
        "$select": "subject,start,end,organizer,bodyPreview,location",
        "$top": 10
    }
    
    response = requests.get(graph_url, headers=headers, params=params)
    
    if response.status_code != 200:
        return {"error": "Failed to fetch events", "status": response.status_code, "details": response.json()}
    
<<<<<<< HEAD
    return cal_utils.get_events_from_outlook(response.json())
=======
    return utils.cal_utils.get_events_from_outlook(response.json())
>>>>>>> 2ac424f011da62b5d6990ac92ac08cca9b79f65f
    #return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
