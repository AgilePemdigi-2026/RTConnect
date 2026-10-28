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

def after_all(context):
    """Clean up test records created during BDD execution."""
    from database.db import execute
    if getattr(context, 'created_letter_ids', None):
        for pid in context.created_letter_ids:
            execute("DELETE FROM surat_final WHERE pengajuan_id = %s", (pid,))
            execute("DELETE FROM pengajuan_surat WHERE pengajuan_id = %s", (pid,))
    if getattr(context, 'created_session_ids', None):
        for sid in context.created_session_ids:
            execute("DELETE FROM chat_messages WHERE session_id = %s", (sid,))
            execute("DELETE FROM chat_sessions WHERE session_id = %s", (sid,))
    if getattr(context, 'created_user_ids', None):
        for uid in context.created_user_ids:
            execute("DELETE FROM notifikasi WHERE penerima_id = %s", (uid,))
            execute("DELETE FROM users WHERE user_id = %s", (uid,))
