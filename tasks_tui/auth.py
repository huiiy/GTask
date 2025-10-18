
import os
import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Define the scopes required for the Google Tasks API
SCOPES = ['https://www.googleapis.com/auth/tasks']

# Get the user's home directory
HOME_DIR = os.path.expanduser('~')
# Define the directory to store the data
GTASK_DIR = os.path.join(HOME_DIR, '.gtask')

TOKEN_PATH = os.path.join(GTASK_DIR, 'token.json')
CLIENT_SECRETS_PATH = os.path.join(GTASK_DIR, 'client_secrets.json')

def _ensure_dir_exists():
    """Ensures that the .gtask directory exists."""
    if not os.path.exists(GTASK_DIR):
        os.makedirs(GTASK_DIR)

def get_credentials():
    """
    Authenticates with the Google Tasks API using OAuth 2.0.
    """
    _ensure_dir_exists()
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds
