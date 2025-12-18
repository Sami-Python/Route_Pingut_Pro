import os
import datetime
import tempfile
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import api.utils.cal_utils as cal_utils

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configuration
# Expect dependencies to be in the same directory or properly referenced
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
# This scope allows reading calendars and events
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
API_SERVICE_NAME = "calendar"
API_VERSION = "v3"

# Allow OAuth to run over HTTP for local testing
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

@app.get("/")
async def root():
    return {"message": "Welcome to the Google Calendar API. Go to /login to start."}

@app.get("/login")
async def login(request: Request, redirect_url: str = None):
    """
    Initiates the OAuth2 flow.
    """
    # Construct the redirect URI based on the request's base URL
    # or use an environment variable if set
    redirect_uri = str(request.url_for("gcal_callback"))
    print(f"Redirect URI: {redirect_uri}")
    
    # Create the flow using the client secrets file
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    # Generate the authorization URL
    # Pass the redirect_url as state if provided
    kwargs = {"prompt": "consent"}
    if redirect_url:
        kwargs["state"] = redirect_url
        
    auth_url, _ = flow.authorization_url(**kwargs)
    
    return RedirectResponse(auth_url)

@app.get("/callback", name="gcal_callback")
async def callback(request: Request, code: str, state: str = None):
    """
    Handles the OAuth2 callback, exchanges code for token, and redirects to frontend.
    Uses a temporary file to pass the token to avoid URL parameter loops.
    """
    redirect_uri = str(request.url_for("gcal_callback"))
    print(f"Redirect URI: {redirect_uri}")

    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        # Fetch the token using the authorization code
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Redirect logic:
        # 1. If state parameter is present, use it as the redirect URL.
        # 2. Otherwise receive FRONTEND_URL environment variable.
        # 3. Default to localhost:8501.
        
        if state:
            redirect_base = state
        else:
            redirect_base = os.getenv("FRONTEND_URL", "http://localhost:8501")
            
        # Append token and success flag
        # Check if the url already has query params
        if "?" in redirect_base:
            redirect_url = f"{redirect_base}&gcal_auth=success&gcal_access_token={creds.token}"
        else:
            redirect_url = f"{redirect_base}?gcal_auth=success&gcal_access_token={creds.token}"
        
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        print(f"OAuth callback error: {e}")
        return {"error": str(e)}

@app.get("/calendars")
async def get_calendars(token: str):
    """
    Lists the user's calendars.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")

    try:
        # Create credentials object from the access token
        creds = Credentials(token=token)
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)

        # List calendars
        calendar_list = service.calendarList().list().execute()
        return calendar_list.get("items", [])

    except HttpError as error:
        return {"error": str(error)}

@app.get("/events")
async def get_events(token: str, calendar_id: str = "primary"):
    """
    Lists the upcoming 10 events from the specified calendar (default: primary).
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")

    try:
        creds = Credentials(token=token)
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)

        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
<<<<<<< HEAD
        return cal_utils.get_events_from_gcal(events_result.get("items", []))
=======
        return utils.cal_utils.get_events_from_gcal(events_result.get("items", []))
>>>>>>> 2ac424f011da62b5d6990ac92ac08cca9b79f65f

    except HttpError as error:
        return {"error": str(error)}