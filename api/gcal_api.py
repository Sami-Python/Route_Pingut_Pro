import os
import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import utils

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
async def login(request: Request):
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
    auth_url, _ = flow.authorization_url(prompt="consent")
    
    return RedirectResponse(auth_url)

@app.get("/callback", name="gcal_callback")
async def callback(request: Request, code: str):

    """
    Handles the OAuth2 callback, exchanges code for token, and redirects to frontend.
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
        
        # Redirect to Streamlit app with the token
        # Using the same env var convention as graph_api.py
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        # Pass the access_token to the frontend
        redirect_url = f"{frontend_url}?access_token={creds.token}"
        
        return RedirectResponse(url=redirect_url)

    except Exception as e:
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
        return utils.get_events_from_gcal(events_result.get("items", []))

    except HttpError as error:
        return {"error": str(error)}