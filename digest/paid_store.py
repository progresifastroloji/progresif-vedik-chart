"""Kişisel ana sayfa digest'i için bağlam sürümlü önbellek.

digest/store.py'ye (ucretsiz katman) dokunmaz, ayri dosyada ayri tablo.
Amaç: aynı kullanıcı + chart + güncel saatlik bağlam için tek Gemini
çağrısı, aynı bağlamdaki diğer sayfa açılışlarında diskten okuma.

Eski `paid_digest` tablosu geriye dönük uyumluluk için korunur; yeni ana
sayfa yolu sürümlü `homepage_digest` tablosunu kullanır.
"""

import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import date, datetime, timedelta, timezone

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "digest_data", "paid_digest.sqlite3")

GENERATOR_VERSION = "homepage-gemini-v3"
METHODOLOGY_VERSION = "digest-methodology-v4"
LOCK_TIMEOUT_MIN = 10


def _conn():
    path = os.getenv("PAID_DIGEST_DB_PATH", _DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS homepage_digest (
            owner_user_id TEXT NOT NULL,
            chart_id TEXT NOT NULL,
            gun TEXT NOT NULL,
            context_hash TEXT NOT NULL,
            generator_version TEXT NOT NULL,
            methodology_version TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (
                owner_user_id, chart_id, gun, context_hash,
                generator_version, methodology_version
            )
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS homepage_digest_lock (
            lock_key TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """)
    return conn


def _now():
    return datetime.now(timezone.utc)


def get_homepage(owner_user_id, chart_id, d, context_hash,
                 generator_version=GENERATOR_VERSION,
                 methodology_version=METHODOLOGY_VERSION):
    with closing(_conn()) as conn:
        row = conn.execute(
            """SELECT payload_json FROM homepage_digest
               WHERE owner_user_id = ? AND chart_id = ? AND gun = ?
                 AND context_hash = ? AND generator_version = ?
                 AND methodology_version = ?""",
            (owner_user_id, chart_id, d.isoformat(), context_hash,
             generator_version, methodology_version),
        ).fetchone()
    return json.loads(row["payload_json"]) if row else None


def set_homepage(owner_user_id, chart_id, payload, d, context_hash,
                 generator_version=GENERATOR_VERSION,
                 methodology_version=METHODOLOGY_VERSION):
    with closing(_conn()) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO homepage_digest
               (owner_user_id, chart_id, gun, context_hash, generator_version,
                methodology_version, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (owner_user_id, chart_id, d.isoformat(), context_hash,
             generator_version, methodology_version,
             json.dumps(payload, ensure_ascii=False)),
        )
        conn.commit()


def acquire_lock(lock_key, dakika=LOCK_TIMEOUT_MIN):
    owner = uuid.uuid4().hex
    now = _now()
    expires = now + timedelta(minutes=dakika)
    with closing(_conn()) as conn:
        conn.execute("DELETE FROM homepage_digest_lock WHERE expires_at < ?",
                     (now.isoformat(),))
        try:
            conn.execute(
                "INSERT INTO homepage_digest_lock (lock_key, owner, expires_at) VALUES (?, ?, ?)",
                (lock_key, owner, expires.isoformat()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return None
    return owner


def release_lock(lock_key, owner):
    with closing(_conn()) as conn:
        conn.execute(
            "DELETE FROM homepage_digest_lock WHERE lock_key = ? AND owner = ?",
            (lock_key, owner),
        )
        conn.commit()


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
