import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import msal
import requests
from dotenv import load_dotenv
import utils

# Load environment variables
load_dotenv()

app = FastAPI()

# Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTHORITY = os.getenv("AUTHORITY", "https://login.microsoftonline.com/consumers")
REDIRECT_PATH = os.getenv("REDIRECT_PATH", "/callback")
# We'll construct the full redirect URI dynamically or you can set it explicitly
# For localhost testing, it's usually http://localhost:8000/callback

SCOPE = ["User.Read", "Calendars.Read"]

# Build the MSAL app with the client ID, authority, and client secret   
def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=authority or AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache,
    )

# Get the authorization URL for the user to login
def _get_auth_url(redirect_uri: str):
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
    # Construct the redirect URI based on the request's base URL
    # This handles http vs https and port numbers automatically
    if "http" in REDIRECT_PATH:
         redirect_uri = REDIRECT_PATH
    else:
         redirect_uri = str(request.url_for("callback"))
    print(f"Using Redirect URI: {redirect_uri}")
    # If running behind a proxy (like ngrok or docker), you might need to force https or specific host
    # For now, we trust the request.url_for
    
    auth_url = _get_auth_url(redirect_uri)
    print(auth_url)
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request, code: str):
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

@app.get("/events")
async def get_events(token: str):
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Fetch events from the default calendar
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
    
    return utils.get_events_from_outlook(response.json())
    #return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
