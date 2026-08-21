"""Kalici depolama.

Guvenlik sozlesmesi:
  - Ayri ve dogrulanmis DB yolu. Baska bir SQLite dosyasi kirletilmez.
  - Kayitlar generator_version ile sürümlüdur; eski sürüm EZILMEZ.
  - Salt okuma yolu DB dosyasi yoksa onu YARATMAZ.
  - Kilit sureli; AI cagrisi boyunca DB kilitli tutulmaz.
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .keys import GENERATOR_VERSION, SCHEMA_VERSION

DEFAULT_PATH = "digest_data/digest.sqlite3"

# Digest'e ait olmayan, kirletilmemesi gereken bilinen yollar.
_FORBIDDEN_ENV = ("BETA_DB_PATH", "PLACES_DB_PATH", "DATABASE_PATH", "DB_PATH")

LOCK_TIMEOUT_MIN = 10

_SCHEMA = """
CREATE TABLE IF NOT EXISTS digest (
    key                TEXT NOT NULL,
    generator_version  TEXT NOT NULL,
    schema_version     INTEGER NOT NULL,
    layer              TEXT NOT NULL,
    cumle              TEXT NOT NULL,
    odak               TEXT,
    kaynak             TEXT NOT NULL,
    dasha_lord         TEXT,
    dasha_level        TEXT,
    dasha_source       TEXT,
    uretim_ms          INTEGER,
    uretim_zamani      TEXT NOT NULL,
    PRIMARY KEY (key, generator_version)
);
CREATE TABLE IF NOT EXISTS snapshot (
    gun            TEXT PRIMARY KEY,
    payload        TEXT NOT NULL,
    uretim_zamani  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hata (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key             TEXT,
    layer           TEXT,
    asama           TEXT,
    hata_sinifi     TEXT,
    mesaj           TEXT,
    fallback_nedeni TEXT,
    sure_ms         INTEGER,
    zaman           TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kilit (
    ad      TEXT PRIMARY KEY,
    sahip   TEXT NOT NULL,
    alindi  TEXT NOT NULL,
    biter   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_digest_layer ON digest(layer);
CREATE INDEX IF NOT EXISTS idx_hata_zaman ON hata(zaman);
"""


def db_path():
    return os.getenv("DIGEST_DB_PATH", DEFAULT_PATH)


def active_generator():
    return os.getenv("DIGEST_ACTIVE_GENERATOR", GENERATOR_VERSION)


def _now():
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------ yol korumasi

def verify_path():
    """DB yolunu dogrular. Uygun degilse ValueError firlatir."""
    p = Path(db_path()).expanduser()
    resolved = str(p.resolve())

    for env in _FORBIDDEN_ENV:
        other = os.getenv(env)
        if other and str(Path(other).expanduser().resolve()) == resolved:
            raise ValueError(
                "DIGEST_DB_PATH %s ile ayni: %s" % (env, resolved))

    if "digest" not in p.name.lower():
        raise ValueError(
            "DIGEST_DB_PATH dosya adi 'digest' icermeli: %s" % p.name)

    yasak_klasor = ("Haritalar", "Analiz Veri Paketleri", "Dashas",
                    "Rektifikasyon")
    for part in p.parts:
        if part in yasak_klasor:
            raise ValueError(
                "DIGEST_DB_PATH kullanici artefakt klasoru icinde: %s" % part)

    return p


def _ensure_parent():
    p = verify_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def exists():
    """DB dosyasi var mi. YARATMAZ."""
    try:
        return verify_path().exists()
    except ValueError:
        return False


def _conn(create=False):
    if create:
        p = _ensure_parent()
    else:
        p = verify_path()
        if not p.exists():
            return None
    c = sqlite3.connect(str(p), timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init():
    """Semayi kurar. Yalniz yazma yollarindan cagrilir."""
    with _conn(create=True) as c:
        c.executescript(_SCHEMA)


# ------------------------------------------------------------ digest

def put(key, layer, cumle, odak, kaynak, dasha_lord=None,
        dasha_level=None, dasha_source=None, uretim_ms=None,
        generator=None):
    """Sürümlü yazar. Ayni (key, generator) varsa DOKUNMAZ."""
    gen = generator or active_generator()
    with _conn(create=True) as c:
        cur = c.execute(
            "INSERT OR IGNORE INTO digest (key, generator_version, "
            "schema_version, layer, cumle, odak, kaynak, dasha_lord, "
            "dasha_level, dasha_source, uretim_ms, uretim_zamani) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (key, gen, SCHEMA_VERSION, layer, cumle, odak, kaynak,
             dasha_lord, dasha_level, dasha_source, uretim_ms, _now()),
        )
        return cur.rowcount > 0  # False ise kayit zaten vardi


def get(key, generator=None):
    gen = generator or active_generator()
    c = _conn()
    if c is None:
        return None
    with c:
        row = c.execute(
            "SELECT * FROM digest WHERE key=? AND generator_version=?",
            (key, gen)).fetchone()
    if not row:
        return None
    return {
        "cumle": row["cumle"],
        "odak": row["odak"],
        "kaynak": row["kaynak"],
        "dasha_lord": row["dasha_lord"],
        "dasha_level": row["dasha_level"],
        "generator_version": row["generator_version"],
        "uretim_zamani": row["uretim_zamani"],
    }


# ------------------------------------------------------------ snapshot

def put_snapshot(gun, payload):
    with _conn(create=True) as c:
        c.execute(
            "INSERT OR REPLACE INTO snapshot (gun, payload, uretim_zamani) "
            "VALUES (?,?,?)",
            (gun, json.dumps(payload, ensure_ascii=False), _now()))


def get_snapshot(gun):
    c = _conn()
    if c is None:
        return None
    with c:
        row = c.execute(
            "SELECT payload FROM snapshot WHERE gun=?", (gun,)).fetchone()
    return json.loads(row["payload"]) if row else None


def get_snapshots(gunler):
    """Istenen gunlerin tamami varsa liste, eksik varsa None."""
    c = _conn()
    if c is None:
        return None
    keys = [g.isoformat() if hasattr(g, "isoformat") else str(g)
            for g in gunler]
    with c:
        rows = c.execute(
            "SELECT gun, payload FROM snapshot WHERE gun IN (%s)"
            % ",".join("?" * len(keys)), keys).fetchall()
    bulunan = {r["gun"]: json.loads(r["payload"]) for r in rows}
    if len(bulunan) != len(keys):
        return None
    return [bulunan[k] for k in keys]


# ------------------------------------------------------------ hata

def log_error(key, layer, asama, exc=None, fallback_nedeni=None,
              sure_ms=None, mesaj=None):
    """Hatayi kalici kaydeder. Sessiz fallback yoktur."""
    sinif = type(exc).__name__ if exc is not None else None
    msg = mesaj if mesaj is not None else (str(exc)[:500] if exc else None)
    try:
        with _conn(create=True) as c:
            c.execute(
                "INSERT INTO hata (key, layer, asama, hata_sinifi, mesaj, "
                "fallback_nedeni, sure_ms, zaman) VALUES (?,?,?,?,?,?,?,?)",
                (key, layer, asama, sinif, msg, fallback_nedeni,
                 sure_ms, _now()))
    except Exception:
        pass  # hata kaydi uretimi durdurmaz


def recent_errors(n=50):
    c = _conn()
    if c is None:
        return []
    with c:
        rows = c.execute(
            "SELECT * FROM hata ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------ kilit

def acquire_lock(ad, dakika=LOCK_TIMEOUT_MIN):
    """Sureli kilit. Alinamazsa None doner."""
    sahip = uuid.uuid4().hex
    simdi = datetime.now(timezone.utc)
    biter = (simdi + timedelta(minutes=dakika)).isoformat()
    with _conn(create=True) as c:
        c.execute("DELETE FROM kilit WHERE biter < ?", (simdi.isoformat(),))
        try:
            c.execute(
                "INSERT INTO kilit (ad, sahip, alindi, biter) VALUES (?,?,?,?)",
                (ad, sahip, simdi.isoformat(), biter))
        except sqlite3.IntegrityError:
            return None
    return sahip


def release_lock(ad, sahip):
    with _conn(create=True) as c:
        c.execute("DELETE FROM kilit WHERE ad=? AND sahip=?", (ad, sahip))


# ------------------------------------------------------------ bakim

def stats():
    """Salt okuma. DB yoksa yaratmaz."""
    if not exists():
        return {"db_var": False, "yol": db_path(),
                "aktif_generator": active_generator()}
    c = _conn()
    with c:
        rows = c.execute(
            "SELECT layer, kaynak, generator_version, COUNT(*) n FROM digest "
            "GROUP BY layer, kaynak, generator_version").fetchall()
        snaps = c.execute("SELECT COUNT(*) n FROM snapshot").fetchone()["n"]
        hatalar = c.execute("SELECT COUNT(*) n FROM hata").fetchone()["n"]
        kilitler = c.execute("SELECT COUNT(*) n FROM kilit").fetchone()["n"]
    return {
        "db_var": True,
        "yol": db_path(),
        "aktif_generator": active_generator(),
        "digest": [
            {"layer": r["layer"], "kaynak": r["kaynak"],
             "generator": r["generator_version"], "adet": r["n"]}
            for r in rows
        ],
        "snapshot_adedi": snaps,
        "hata_adedi": hatalar,
        "acik_kilit": kilitler,
    }


def prune_snapshots(before_gun_iso):
    """Eski snapshot'lari siler. Gezegen konumlari yeniden hesaplanabilir."""
    with _conn(create=True) as c:
        return c.execute(
            "DELETE FROM snapshot WHERE gun < ?", (before_gun_iso,)).rowcount


def prune_errors(before_iso):
    with _conn(create=True) as c:
        return c.execute("DELETE FROM hata WHERE zaman < ?",
                         (before_iso,)).rowcount
