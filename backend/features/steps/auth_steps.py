import random
from behave import given, when, then
from database.db import query_one

@given('I prepare a unique citizen registration payload')
@given('I prepare a unique citizen registration payload:')
def step_prepare_unique_registration(context):
    rand_nik = f"351508{random.randint(1000000000, 9999999999)}"
    rand_email = f"warga_{rand_nik}@example.test"
    payload = {row['field']: row['value'] for row in context.table}
    payload['nik'] = rand_nik
    payload['email'] = rand_email
    context.payload = payload
    context.last_created_nik = rand_nik

@given('I prepare a citizen registration payload with NIK "{nik}", email "{email}", and password "{password}"')
def step_prepare_registration_with_params(context, nik, email, password):
    context.payload = {
        'nik': nik,
        'nama_lengkap': 'Warga Uji Format',
        'email': email,
        'password': password,
        'nomor_telepon': '081299887766',
        'alamat': 'Jl. Asri No. 5 RT 05 RW 02'
    }

@given('an existing resident user with email "{email}" is registered')
def step_ensure_resident_exists(context, email):
    user = query_one("SELECT user_id, email FROM users WHERE email = %s", (email,))
    assert user is not None, f"Resident {email} does not exist in seed data"

@when('I submit a registration with an already registered email "{email}"')
def step_submit_duplicate_email(context, email):
    rand_nik = f"351508{random.randint(1000000000, 9999999999)}"
    context.payload = {
        'nik': rand_nik,
        'nama_lengkap': 'Duplikasi Warga',
        'email': email,
        'password': 'PasswordKuat#2026',
        'nomor_telepon': '081233445566',
        'alamat': 'Jl. Melati Blok B-1'
    }
    context.last_response = context.client.post('/api/v1/auth/register', json=context.payload)
    context.last_json = context.last_response.get_json(silent=True) or {}

@when('I send a POST request to "{endpoint}" with the payload')
def step_post_with_payload(context, endpoint):
    context.last_response = context.client.post(endpoint, json=context.payload)
    context.last_json = context.last_response.get_json(silent=True) or {}

@when('I authenticate with identity "{identity}" and password "{password}"')
def step_login_identity(context, identity, password):
    context.last_response = context.client.post('/api/v1/auth/login', json={
        'identity': identity,
        'password': password
    })
    context.last_json = context.last_response.get_json(silent=True) or {}
    if context.last_response.status_code == 200 and 'data' in context.last_json:
        token = context.last_json['data'].get('token')
        if token:
            context.auth_headers = {'Authorization': f'Bearer {token}'}

@then('the response should contain a valid JWT token')
def step_assert_jwt_token(context):
    token = context.last_json.get('data', {}).get('token')
    assert token is not None and len(token) > 20, f"Token invalid or not found: {token}"

@then('the registered user should exist in the database with role "{expected_role}"')
def step_assert_user_in_db(context, expected_role):
    nik = context.last_created_nik
    user = query_one("SELECT user_id, nik, role FROM users WHERE nik = %s", (nik,))
    assert user is not None, f"User with NIK {nik} not found in DB"
    assert user['role'] == expected_role, f"Expected role {expected_role}, got {user['role']}"
    context.created_user_ids.append(user['user_id'])
