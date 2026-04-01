from fastapi import FastAPI
from pydantic import BaseModel

from _shared_db import db_conn, make_id

app = FastAPI(title='tof_local_knowledge_auth_api', version='0.2.0')

ROLES = [
    'system_admin',
    'source_admin',
    'knowledge_user',
    'auditor',
    'service_account',
]


class UserUpsert(BaseModel):
    username: str
    display_name: str | None = None
    is_active: bool = True


class GrantUpsert(BaseModel):
    username: str
    source_id: str
    role_name: str


@app.get('/health')
def health():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            cur.fetchone()
    return {'status': 'ok', 'service': 'auth_api'}


@app.get('/roles')
def roles():
    return {'roles': ROLES}


@app.get('/users')
def list_users():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id, username, display_name, is_active, created_at FROM app_users ORDER BY username')
            return {'users': cur.fetchall()}


@app.post('/users/upsert')
def upsert_user(payload: UserUpsert):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM app_users WHERE username = %s', (payload.username,))
            row = cur.fetchone()
            user_id = row['user_id'] if row else make_id('user')
            cur.execute(
                '''
                INSERT INTO app_users (user_id, username, display_name, is_active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE
                SET display_name = EXCLUDED.display_name,
                    is_active = EXCLUDED.is_active
                ''',
                (user_id, payload.username, payload.display_name, payload.is_active),
            )
    return {'status': 'ok', 'user_id': user_id}


@app.get('/grants')
def list_grants():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT g.grant_id, u.username, g.source_id, g.role_name, g.created_at
                FROM user_source_grants g
                JOIN app_users u ON u.user_id = g.user_id
                ORDER BY u.username, g.source_id, g.role_name
                '''
            )
            return {'grants': cur.fetchall()}


@app.post('/grants/upsert')
def upsert_grant(payload: GrantUpsert):
    if payload.role_name not in ROLES:
        return {'status': 'error', 'detail': 'unknown_role'}
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM app_users WHERE username = %s', (payload.username,))
            row = cur.fetchone()
            if not row:
                return {'status': 'error', 'detail': 'unknown_user'}
            user_id = row['user_id']
            cur.execute(
                '''
                SELECT grant_id FROM user_source_grants
                WHERE user_id = %s AND source_id = %s AND role_name = %s
                ''',
                (user_id, payload.source_id, payload.role_name),
            )
            existing = cur.fetchone()
            grant_id = existing['grant_id'] if existing else make_id('grant')
            if not existing:
                cur.execute(
                    'INSERT INTO user_source_grants (grant_id, user_id, source_id, role_name) VALUES (%s, %s, %s, %s)',
                    (grant_id, user_id, payload.source_id, payload.role_name),
                )
    return {'status': 'ok', 'grant_id': grant_id}
