from __future__ import annotations

import os
from contextlib import contextmanager
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row


def database_url() -> str:
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://tof_local_knowledge:local_dev_password@postgres:5432/tof_local_knowledge',
    )


@contextmanager
def db_conn():
    conn = psycopg.connect(database_url(), autocommit=True, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def make_id(prefix: str) -> str:
    return f'{prefix}_{uuid4().hex}'
