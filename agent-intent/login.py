import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = FastAPI()

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

REDIRECT_URI = "http://localhost:8005/callback"


flow = None
user_tokens = {}

@app.get("/")
async def root():
    return {"message": "SkyNode AI Server is running. Go to /login to connect Google Calendar."}

@app.get("/login")
async def login():
    global flow
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    global flow
    if flow is None:
        return {"error": "Flow is missing. Please restart /login"}

    code = request.query_params.get("code")
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        user_tokens["current_user"] = credentials.to_json()
        with open("token.json", "w") as token_file:
            token_file.write(credentials.to_json())
            
        return {
            "status": "Success", 
            "message": "Connected to Google Calendar! Now go to /get-calendar"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/get-calendar")
async def get_calendar():
    if "current_user" not in user_tokens:
        if os.path.exists("token.json"):
            with open("token.json", "r") as f:
                user_tokens["current_user"] = f.read()
        else:
            return {"error": "Please login first at /login"}
    
    from google.oauth2.credentials import Credentials
    creds_data = json.loads(user_tokens["current_user"])
    creds = Credentials.from_authorized_user_info(creds_data)
    
    service = build('calendar', 'v3', credentials=creds)
    
    import datetime
    now = datetime.datetime.utcnow().isoformat() + 'Z' 

    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=10, singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    return {"calendar_events": events}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)