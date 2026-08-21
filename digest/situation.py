"""Deterministik durum paketi.

Kaynak: vedic_chart.calculate_chart. HTTP cagrisi, kukla dogum verisi ve
tam harita uretimi YOKTUR. Yalniz gezegen burc indeksleri okunur.

Gezegen boylamlari swe.calc_ut ile yalniz Julian Day'e baglidir; enlem/
boylam sadece Lagna'yi etkiler ve Lagna kullanilmaz. Bu nedenle sabit
koordinat sonucu degistirmez.

Kalici durum yaratmaz: dosya yazmaz, chart artefakti uretmez, beta
kayitlarina dokunmaz.
"""

from collections import Counter

from .keys import (
    house_from,
    month_days,
    quality,
    tz_offset_hours,
    week_days,
)

# Lagna kullanilmadigi icin sonucu etkilemez; yalniz imza gereklidir.
REF_LAT = 41.0082
REF_LON = 28.9784

# calculate_chart 'Sun / Gunes' gibi adlar dondurur; abbr temizdir.
ABBR = {
    "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury",
    "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn",
    "Ra": "Rahu", "Ke": "Ketu",
}

FAST_PLANETS = ("Sun", "Mercury", "Venus", "Mars")
SLOW_PLANETS = ("Saturn", "Jupiter", "Rahu", "Ketu")

# Baskin ev beraberliginde oncelik.
FAST_PRIORITY = ("Sun", "Mars", "Venus", "Mercury")


def planet_signs(d):
    """Verilen gun icin 12:00 Istanbul gezegen burc indeksleri.

    Doner: {"date": "YYYY-MM-DD", "planets": {"Sun": 4, "Moon": 5, ...}}
    """
    from vedic_chart import calculate_chart

    chart = calculate_chart(
        d.year, d.month, d.day,
        12, 0,
        tz_offset_hours(d),
        REF_LAT, REF_LON,
    )

    planets = {}
    for p in chart.get("planets", []):
        name = ABBR.get(p.get("abbr"))
        if name is None:
            continue
        planets[name] = int(p["sign_index"])

    if "Moon" not in planets:
        raise RuntimeError("transit Ay hesaplanamadi")

    return {"date": d.isoformat(), "planets": planets}


# ------------------------------------------------------------ yardimci

def _house(snap, natal_idx, planet):
    idx = snap["planets"].get(planet)
    return None if idx is None else house_from(natal_idx, idx)


def _dominant(counter, owner):
    """En cok gorulen ev. Beraberlikte FAST_PRIORITY belirler."""
    if not counter:
        return None
    best = max(counter.values())
    tied = [h for h, c in counter.items() if c == best]
    if len(tied) == 1:
        return tied[0]
    for pref in FAST_PRIORITY:
        for h in tied:
            if pref in owner.get(h, set()):
                return h
    return sorted(tied)[0]


# ------------------------------------------------------------ gunluk

def daily_situation(snap, natal_idx):
    house = _house(snap, natal_idx, "Moon")
    return {
        "layer": "daily",
        "natal_sign_index": int(natal_idx),
        "ay_evi": house,
        "gun_kalitesi": quality(house),
        "snapshot_gunleri": [snap["date"]],
    }


# ------------------------------------------------------------ haftalik

def weekly_situation(snaps, natal_idx, lord, dasha_level):
    """snaps: haftanin yedi gunune ait snapshot listesi."""
    counter = Counter()
    owner = {}
    ay_evleri = []

    for s in snaps:
        mh = _house(s, natal_idx, "Moon")
        if mh:
            ay_evleri.append(mh)
        for planet in FAST_PLANETS:
            h = _house(s, natal_idx, planet)
            if h:
                counter[h] += 1
                owner.setdefault(h, set()).add(planet)

    baskin = _dominant(counter, owner)
    if baskin is None:
        baskin = ay_evleri[0] if ay_evleri else 1

    return {
        "layer": "weekly",
        "natal_sign_index": int(natal_idx),
        "baskin_ev": baskin,
        "gun_kalitesi": quality(baskin),
        "ay_evleri": ay_evleri,
        "ay_burc_degisimi": len(set(ay_evleri)) > 1,
        "dasha_lord": lord,
        "dasha_level": dasha_level,
        "snapshot_gunleri": [s["date"] for s in snaps],
    }


# ------------------------------------------------------------- aylik

def monthly_situation(snaps, natal_idx, lord, dasha_level):
    """snaps: takvim ayinin butun gunlerine ait snapshot listesi."""
    gunes = Counter()
    for s in snaps:
        h = _house(s, natal_idx, "Sun")
        if h:
            gunes[h] += 1
    gunes_evi = gunes.most_common(1)[0][0] if gunes else 1

    yavas = {}
    yavas_degisim = {}
    for planet in SLOW_PLANETS:
        c = Counter()
        for s in snaps:
            h = _house(s, natal_idx, planet)
            if h:
                c[h] += 1
        if c:
            yavas[planet] = c.most_common(1)[0][0]
            yavas_degisim[planet] = len(c) > 1

    # Sade Sati: Saturn'un 12/1/2. evde oldugu gun sayisi cogunluksa aktif.
    sat_gun = 0
    for s in snaps:
        h = _house(s, natal_idx, "Saturn")
        if h in (12, 1, 2):
            sat_gun += 1
    sade_sati = bool(snaps) and sat_gun * 2 > len(snaps)

    return {
        "layer": "monthly",
        "natal_sign_index": int(natal_idx),
        "gunes_evi": gunes_evi,
        "gun_kalitesi": quality(gunes_evi),
        "gunes_burc_degisimi": len(gunes) > 1,
        "yavas_gezegen_evleri": yavas,
        "yavas_gezegen_degisimi": yavas_degisim,
        "sade_sati": sade_sati,
        "sade_sati_gun_sayisi": sat_gun,
        "dasha_lord": lord,
        "dasha_level": dasha_level,
        "snapshot_gunleri": [s["date"] for s in snaps],
    }


# ------------------------------------------------------------ toplayici

def required_days(layer, d):
    """Katmanin ihtiyac duydugu snapshot gunleri."""
    if layer == "daily":
        return [d]
    if layer == "weekly":
        return week_days(d)
    if layer == "monthly":
        return month_days(d)
    raise ValueError("bilinmeyen katman: %s" % layer)


def build_situation(layer, snaps, natal_idx, lord=None, dasha_level=None):
    if layer == "daily":
        return daily_situation(snaps[0], natal_idx)
    if layer == "weekly":
        return weekly_situation(snaps, natal_idx, lord, dasha_level)
    if layer == "monthly":
        return monthly_situation(snaps, natal_idx, lord, dasha_level)
    raise ValueError("bilinmeyen katman: %s" % layer)
