import os
import sys

# Ensure backend root is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from config import Config

def before_all(context):
    """Initializes the Flask test client and test configuration."""
    if not Config.RT_SIGNING_PIN_HASH and not Config.IS_PRODUCTION:
        import bcrypt
        Config.RT_SIGNING_PIN_HASH = bcrypt.hashpw(b'123456', bcrypt.gensalt()).decode('utf-8')
    if not Config.RT_WHATSAPP_NUMBER and not Config.IS_PRODUCTION:
        Config.RT_WHATSAPP_NUMBER = '6281234567890'

    context.app = create_app()
    context.client = context.app.test_client()
    context.auth_headers = {}
    context.last_response = None
    context.last_json = None
    context.created_user_ids = []
    context.created_letter_ids = []
    context.created_session_ids = []

def before_scenario(context, scenario):
    """Reset context variables before each scenario."""
    context.auth_headers = {}
    context.last_response = None
    context.last_json = None
    context.payload = {}
