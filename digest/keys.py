"""Anahtar semasi, sabitler ve Europe/Istanbul tarih yardimcilari.

Iki ayri zaman kavrami vardir:
  - Yayin ani  : 00:00 Europe/Istanbul (yeni digest kullaniciya acilir)
  - Snapshot ani: 12:00 Europe/Istanbul (o gunun gezegen goruntusu)

Sabit UTC+3 yazilmaz; ZoneInfo gercek tarihsel farki cozer.
"""

from datetime import date, datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    from backports.zoneinfo import ZoneInfo

IST = ZoneInfo("Europe/Istanbul")

SCHEMA_VERSION = 2
GENERATOR_VERSION = "digest_rules_v2"

SNAPSHOT_HOUR = 12  # o gune ait gezegen goruntusunun ornekleme saati

SIGN_TR = [
    "Koc", "Boga", "Ikizler", "Yengec", "Aslan", "Basak",
    "Terazi", "Akrep", "Yay", "Oglak", "Kova", "Balik",
]

DASHA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]

# Katman -> hangi Vimshottari seviyesinin yan parcayi besledigi.
LAYER_DASHA_LEVEL = {
    "daily": None,          # gunluk katmanda dasha yan parcasi yoktur
    "weekly": "pratyantar",
    "monthly": "antara",
}

DASHA_SOURCE = "dashas.vimshottari.current_active"

LAYERS = ("daily", "weekly", "monthly")

# Gochara kalite eslemesi (onaylandi).
SUPPORTIVE = {1, 3, 6, 7, 10, 11}
CAUTIOUS = {4, 8, 12}
NEUTRAL = {2, 5, 9}


def quality(house):
    if house in SUPPORTIVE:
        return "destekli"
    if house in CAUTIOUS:
        return "dikkatli"
    return "notr"


def house_from(natal_sign_index, transit_sign_index):
    """Natal burctan transit burca kacinci ev. 1-12 doner."""
    return (int(transit_sign_index) - int(natal_sign_index)) % 12 + 1


def normalize_lord(name):
    """'Rahu (True)' -> 'Rahu'. Taninmazsa None."""
    if not name:
        return None
    n = str(name).strip()
    for lord in DASHA_LORDS:
        if n.lower().startswith(lord.lower()):
            return lord
    return None


# ------------------------------------------------------------ zaman

def today_ist():
    """Yayin anina gore bugunun Istanbul tarihi."""
    return datetime.now(IST).date()


def current_hour_ist():
    """Güncel yorum için İstanbul saatinin saatlik önbellek kovası."""
    return datetime.now(IST).replace(minute=0, second=0, microsecond=0)


def tz_offset_hours(d):
    """Verilen gun icin Istanbul'un gercek UTC farki (saat)."""
    dt = datetime(d.year, d.month, d.day, SNAPSHOT_HOUR, 0, tzinfo=IST)
    return dt.utcoffset().total_seconds() / 3600.0


def week_start(d):
    """ISO haftasinin pazartesisi."""
    return d - timedelta(days=d.weekday())


def week_days(d):
    """Haftanin yedi gunu, pazartesiden."""
    s = week_start(d)
    return [s + timedelta(days=i) for i in range(7)]


def month_start(d):
    return d.replace(day=1)


def month_days(d):
    """Takvim ayinin butun gunleri."""
    s = month_start(d)
    if s.month == 12:
        nxt = date(s.year + 1, 1, 1)
    else:
        nxt = date(s.year, s.month + 1, 1)
    n = (nxt - s).days
    return [s + timedelta(days=i) for i in range(n)]


def iso_week(d):
    y, w, _ = d.isocalendar()
    return "%d-W%02d" % (y, w)


# ------------------------------------------------------------ anahtar

def daily_key(d, sign_index):
    return "digest:daily:%s:%02d" % (d.isoformat(), int(sign_index))


def weekly_key(d, sign_index, lord):
    return "digest:weekly:%s:%02d:%s" % (iso_week(d), int(sign_index), lord)


def monthly_key(d, sign_index, lord):
    return "digest:monthly:%s:%02d:%s" % (
        d.strftime("%Y-%m"), int(sign_index), lord)


def build_key(layer, d, sign_index, lord=None):
    if layer == "daily":
        return daily_key(d, sign_index)
    if layer == "weekly":
        return weekly_key(d, sign_index, lord)
    if layer == "monthly":
        return monthly_key(d, sign_index, lord)
    raise ValueError("bilinmeyen katman: %s" % layer)


def rotation_seed(layer, d):
    """Deterministik alternatif secimi.

    Gunluk her gun, haftalik hafta boyunca, aylik ay boyunca sabit.
    """
    if layer == "daily":
        return d.toordinal()
    if layer == "weekly":
        return week_start(d).toordinal()
    if layer == "monthly":
        return month_start(d).toordinal()
    raise ValueError("bilinmeyen katman: %s" % layer)
