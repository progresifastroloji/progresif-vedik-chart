"""Ucretli kisisel digest icin gunluk onbellek.

digest/store.py'ye (ucretsiz katman) dokunmaz, ayri dosyada ayri tablo.
Amac: ayni chart_id icin gunde bir Gemini cagrisi, geri kalan
sayfa acilislarinda diskten oku.

Sema kasitli kucuk: chart_id + tarih -> uretilen JSON metni.
"""

import json
import os
import sqlite3
from contextlib import closing
from datetime import date

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "digest_data", "paid_digest.sqlite3")


def _conn():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paid_digest (
            chart_id TEXT NOT NULL,
            gun TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (chart_id, gun)
        )
    """)
    return conn


def get(chart_id, d=None):
    d = d or date.today()
    with closing(_conn()) as conn:
        row = conn.execute(
            "SELECT payload_json FROM paid_digest WHERE chart_id = ? AND gun = ?",
            (chart_id, d.isoformat()),
        ).fetchone()
    if not row:
        return None
    return json.loads(row["payload_json"])


def set(chart_id, payload, d=None):
    d = d or date.today()
    with closing(_conn()) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO paid_digest (chart_id, gun, payload_json) VALUES (?, ?, ?)",
            (chart_id, d.isoformat(), json.dumps(payload, ensure_ascii=False)),
        )
        conn.commit()
