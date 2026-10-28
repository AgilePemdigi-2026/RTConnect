import json
import re
from behave import given, when, then

def resolve_field(data, path):
    """Resolve dot-separated path in nested dictionary/list."""
    parts = path.split('.')
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if idx < len(current) else None
        else:
            return None
    return current

@given('the RTConnect backend application is ready')
def step_backend_ready(context):
    assert context.client is not None, "Flask test client is not initialized"

@given('I am authenticated as "{identity}" with password "{password}"')
def step_authenticate(context, identity, password):
    res = context.client.post('/api/v1/auth/login', json={
        'identity': identity,
        'password': password
    })
    assert res.status_code == 200, f"Login failed for {identity}: {res.data}"
    token = res.get_json()['data']['token']
    context.auth_headers = {'Authorization': f'Bearer {token}'}

@when('I send an authenticated GET request to "{endpoint}"')
def step_authenticated_get(context, endpoint):
    context.last_response = context.client.get(endpoint, headers=context.auth_headers)
    context.last_json = context.last_response.get_json(silent=True) or {}

@when('I send an unauthenticated GET request to "{endpoint}"')
def step_unauthenticated_get(context, endpoint):
    context.last_response = context.client.get(endpoint)
    context.last_json = context.last_response.get_json(silent=True) or {}

@then('the response status code should be {status_code:d}')
def step_assert_status_code(context, status_code):
    actual = context.last_response.status_code
    assert actual == status_code, \
        f"Expected HTTP {status_code}, got {actual}. Body: {context.last_response.data}"

@then('the response JSON should indicate success')
def step_assert_success(context):
    assert context.last_json.get('success') is True, \
        f"Expected success=True, got {context.last_json}"

@then('the response JSON should indicate failure')
def step_assert_failure(context):
    assert context.last_json.get('success') is False, \
        f"Expected success=False, got {context.last_json}"

@then('the response field "{field_path}" should be "{expected_value}"')
def step_assert_field_value(context, field_path, expected_value):
    val = resolve_field(context.last_json, field_path)
    assert str(val) == expected_value, \
        f"Field '{field_path}': expected '{expected_value}', got '{val}' (JSON: {context.last_json})"

@then('the response field "{field_path}" should not be empty')
def step_assert_field_not_empty(context, field_path):
    val = resolve_field(context.last_json, field_path)
    assert val is not None and val != '' and val != [] and val != {}, \
        f"Field '{field_path}' is empty or None: {val}"

@then('the response field "{field_path}" should be a non-empty list')
def step_assert_field_non_empty_list(context, field_path):
    val = resolve_field(context.last_json, field_path)
    assert isinstance(val, list) and len(val) > 0, \
        f"Field '{field_path}' is not a non-empty list: {val}"

@then('the response field "{field_path}" should be a list')
def step_assert_field_list(context, field_path):
    val = resolve_field(context.last_json, field_path)
    assert isinstance(val, list), f"Field '{field_path}' is not a list: {val}"

@then('the response field "{field_path}" should be an integer')
def step_assert_field_integer(context, field_path):
    val = resolve_field(context.last_json, field_path)
    assert isinstance(val, int), f"Field '{field_path}' is not an integer: {val}"
