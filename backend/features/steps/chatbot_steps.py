from behave import given, when, then
from database.db import query_all, query_one, execute
from common_steps import resolve_field

@when('I ask the chatbot: "{query}"')
def step_ask_chatbot(context, query):
    payload = {'query': query}
    if getattr(context, 'active_session_id', None):
        payload['session_id'] = context.active_session_id

    context.last_response = context.client.post('/api/v1/chatbot/query', headers=context.auth_headers, json=payload)
    context.last_json = context.last_response.get_json(silent=True) or {}
    if context.last_response.status_code == 200:
        sid = context.last_json.get('data', {}).get('session_id')
        if sid:
            context.active_session_id = sid
            context.created_session_ids.append(sid)

@then('the response field "{field_path}" should be greater than or equal to {min_val:f}')
def step_assert_field_gte(context, field_path, min_val):
    val = resolve_field(context.last_json, field_path)
    assert val is not None, f"Field '{field_path}' is None"
    assert float(val) >= min_val, f"Expected {field_path} >= {min_val}, got {val}"

@then('the response field "{field_path}" should be less than {max_val:f}')
def step_assert_field_lt(context, field_path, max_val):
    val = resolve_field(context.last_json, field_path)
    assert val is not None, f"Field '{field_path}' is None"
    assert float(val) < max_val, f"Expected {field_path} < {max_val}, got {val}"

@then('the response field "{field_path}" should be false')
def step_assert_field_false(context, field_path):
    val = resolve_field(context.last_json, field_path)
    assert val is False, f"Expected {field_path} to be False, got {val}"

@then('the response field "{field_path}" should be true')
def step_assert_field_true(context, field_path):
    val = resolve_field(context.last_json, field_path)
    assert val is True, f"Expected {field_path} to be True, got {val}"

@then('the response field "{field_path}" should contain "{substring}"')
def step_assert_field_contains(context, field_path, substring):
    val = resolve_field(context.last_json, field_path)
    assert val is not None and substring in str(val), \
        f"Expected substring '{substring}' in field '{field_path}', got '{val}'"

@then('the chat message should be recorded in database table "chat_messages" for this session')
def step_assert_chat_message_recorded(context):
    sid = getattr(context, 'active_session_id', None)
    assert sid is not None, "No active session ID"
    msgs = query_all("SELECT message_id, pengirim, isi_pesan FROM chat_messages WHERE session_id = %s", (sid,))
    assert len(msgs) >= 2, f"Expected at least 2 messages (warga & AI), got {len(msgs)}"

@given('an active chat session exists for "{email}"')
def step_ensure_chat_session(context, email):
    user = query_one("SELECT user_id FROM users WHERE email = %s", (email,))
    assert user is not None
    sess = query_one("SELECT session_id FROM chat_sessions WHERE warga_id = %s ORDER BY session_id DESC LIMIT 1", (user['user_id'],))
    if not sess:
        sid = execute("INSERT INTO chat_sessions (warga_id, status_sesi) VALUES (%s, 'berlangsung')", (user['user_id'],))
        execute("INSERT INTO chat_messages (session_id, pengirim, isi_pesan) VALUES (%s, 'warga', 'Halo TanyaRT')", (sid,))
        context.active_session_id = sid
    else:
        context.active_session_id = sess['session_id']

@when('I send an authenticated GET request for messages of the active chat session')
def step_get_session_messages(context):
    sid = getattr(context, 'active_session_id', 1)
    context.last_response = context.client.get(f'/api/v1/chatbot/sessions/{sid}/messages', headers=context.auth_headers)
    context.last_json = context.last_response.get_json(silent=True) or {}
