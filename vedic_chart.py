#!/usr/bin/env python3
"""
Vedik Astroloji Harita Hesaplayıcı
===================================
Swiss Ephemeris tabanlı, Lahiri Ayanamsa, Whole Sign ev sistemi.
Çıktılar: Gezegen pozisyonları, Nakshatra, Vimshottari Dasha, D9 Navamsha
"""

import swisseph as swe

# ── Sabitler ──────────────────────────────────────────────────────────────

SIGNS_TR = [
    "Koç (Aries)", "Boğa (Taurus)", "İkizler (Gemini)",
    "Yengeç (Cancer)", "Aslan (Leo)", "Başak (Virgo)",
    "Terazi (Libra)", "Akrep (Scorpio)", "Yay (Sagittarius)",
    "Oğlak (Capricorn)", "Kova (Aquarius)", "Balık (Pisces)"
]

SIGNS_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury")
]

NAKSHATRA_SPAN = 13.0 + 20.0 / 60.0  # 13°20'

# Vimshottari Dasha sırası ve süreleri (yıl)
DASHA_ORDER = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
    ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)
]
DASHA_TOTAL = 120  # yıl

PLANETS = [
    (swe.SUN, "Sun / Güneş", "Su"),
    (swe.MOON, "Moon / Ay", "Mo"),
    (swe.MARS, "Mars / Mangal", "Ma"),
    (swe.MERCURY, "Mercury / Budha", "Me"),
    (swe.JUPITER, "Jupiter / Guru", "Ju"),
    (swe.VENUS, "Venus / Shukra", "Ve"),
    (swe.SATURN, "Saturn / Shani", "Sa"),
]

NODES = [
    (swe.TRUE_NODE, "Rahu (True)", "Ra"),
]


# ── Yardımcı Fonksiyonlar ────────────────────────────────────────────────

def dms_str(degrees):
    """Derece → D°M'S\" formatı"""
    d = int(degrees)
    m_full = (degrees - d) * 60
    m = int(m_full)
    s = (m_full - m) * 60
    return f"{d}°{m:02d}'{s:04.1f}\""


def get_sign_index(longitude):
    """Boylam → burç indeksi (0-11)"""
    return int(longitude / 30.0)


def get_sign_degree(longitude):
    """Boylam → burç içindeki derece"""
    return longitude % 30.0


def get_nakshatra(longitude):
    """Boylam → nakshatra bilgisi"""
    nak_index = int(longitude / NAKSHATRA_SPAN)
    if nak_index >= 27:
        nak_index = 26
    nak_degree = longitude - (nak_index * NAKSHATRA_SPAN)
    pada = int(nak_degree / (NAKSHATRA_SPAN / 4.0)) + 1
    if pada > 4:
        pada = 4
    name, lord = NAKSHATRAS[nak_index]
    return {
        "index": nak_index,
        "name": name,
        "lord": lord,
        "pada": pada,
        "degree_in_nakshatra": nak_degree
    }


def get_navamsha_sign(longitude):
    """
    D9 Navamsha hesaplama:
    Her burç 9 parçaya bölünür (3°20' = 3.3333°)
    Ateş burçları (0,4,8) → Koç'tan başlar
    Toprak burçları (1,5,9) → Oğlak'tan başlar
    Hava burçları (2,6,10) → Terazi'den başlar
    Su burçları (3,7,11) → Yengeç'ten başlar
    """
    sign_idx = get_sign_index(longitude)
    degree_in_sign = get_sign_degree(longitude)
    navamsha_part = int(degree_in_sign / (30.0 / 9.0))
    if navamsha_part >= 9:
        navamsha_part = 8

    element = sign_idx % 4  # 0=fire, 1=earth, 2=air, 3=water
    start_signs = {0: 0, 1: 9, 2: 6, 3: 3}  # Aries, Cap, Libra, Cancer
    navamsha_sign = (start_signs[element] + navamsha_part) % 12
    navamsha_degree = (degree_in_sign % (30.0 / 9.0)) * 9.0  # scale to 30°

    return navamsha_sign, navamsha_degree


def is_retrograde(speed):
    return speed < 0


def jd_to_date(jd):
    """Julian Day → tarih string"""
    y, m, d, h = swe.revjul(jd)
    hour = int(h)
    minute = int((h - hour) * 60)
    return f"{d:02d}.{m:02d}.{y} {hour:02d}:{minute:02d}"


def date_to_jd(year, month, day, hour, minute, tz_offset, second=0):
    """Tarih → Julian Day (UTC'ye çevrilerek)"""
    ut_hour = hour + minute / 60.0 + second / 3600.0 - tz_offset
    jd = swe.julday(year, month, day, ut_hour)
    return jd


def calc_vimshottari_dasha(moon_longitude, birth_jd):
    """
    Vimshottari Dasha hesaplama.
    Ay'ın nakshatra'sındaki pozisyonuna göre Maha Dasha başlangıçları hesaplanır.
    """
    nak = get_nakshatra(moon_longitude)
    nak_lord = nak["lord"]

    lord_index = None
    for i, (lord, _) in enumerate(DASHA_ORDER):
        if lord == nak_lord:
            lord_index = i
            break

    elapsed_fraction = nak["degree_in_nakshatra"] / NAKSHATRA_SPAN
    remaining_fraction = 1.0 - elapsed_fraction

    dashas = []
    current_jd = birth_jd

    first_lord, first_years = DASHA_ORDER[lord_index]
    remaining_years = first_years * remaining_fraction
    remaining_days = remaining_years * 365.25
    end_jd = current_jd + remaining_days

    dashas.append({
        "lord": first_lord,
        "total_years": first_years,
        "effective_years": round(remaining_years, 2),
        "start": jd_to_date(current_jd),
        "end": jd_to_date(end_jd),
        "is_birth_dasha": True
    })
    current_jd = end_jd

    for cycle in range(2):
        for i in range(9):
            idx = (lord_index + 1 + i) % 9
            lord, years = DASHA_ORDER[idx]
            days = years * 365.25
            end_jd = current_jd + days
            dashas.append({
                "lord": lord,
                "total_years": years,
                "effective_years": years,
                "start": jd_to_date(current_jd),
                "end": jd_to_date(end_jd),
                "is_birth_dasha": False
            })
            current_jd = end_jd

    return dashas


# ── Ana Hesaplama ────────────────────────────────────────────────────────

def calculate_chart(year, month, day, hour, minute, tz_offset, lat, lon, second=0):
    """
    Tam Vedik harita hesaplama.

    Parametreler:
        year, month, day: Doğum tarihi
        hour, minute, second: Doğum saati (yerel saat)
        tz_offset: UTC farkı (örn. Türkiye için 3.0)
        lat, lon: Doğum yeri koordinatları
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    jd = date_to_jd(year, month, day, hour, minute, tz_offset, second)

    # Ascendant (Lagna)
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', flags)
    asc_longitude = ascmc[0]
    asc_sign_idx = get_sign_index(asc_longitude)
    asc_degree = get_sign_degree(asc_longitude)
    asc_nakshatra = get_nakshatra(asc_longitude)

    lagna_info = {
        "longitude": asc_longitude,
        "sign_index": asc_sign_idx,
        "sign": SIGNS_TR[asc_sign_idx],
        "sign_en": SIGNS_EN[asc_sign_idx],
        "degree": asc_degree,
        "degree_str": dms_str(asc_degree),
        "nakshatra": asc_nakshatra
    }

    # Gezegen Pozisyonları
    planet_data = []

    all_planets = PLANETS + NODES
    for planet_id, name, abbr in all_planets:
        pos, ret = swe.calc_ut(jd, planet_id, flags)
        longitude = pos[0]
        speed = pos[3]
        retro = is_retrograde(speed) if planet_id not in (swe.SUN, swe.MOON) else False

        sign_idx = get_sign_index(longitude)
        degree_in_sign = get_sign_degree(longitude)
        nak = get_nakshatra(longitude)

        nav_sign, nav_degree = get_navamsha_sign(longitude)

        house = ((sign_idx - asc_sign_idx) % 12) + 1

        planet_data.append({
            "id": planet_id,
            "name": name,
            "abbr": abbr,
            "longitude": longitude,
            "sign_index": sign_idx,
            "sign": SIGNS_TR[sign_idx],
            "sign_en": SIGNS_EN[sign_idx],
            "degree": degree_in_sign,
            "degree_str": dms_str(degree_in_sign),
            "retrograde": retro,
            "speed": speed,
            "house": house,
            "nakshatra": nak,
            "navamsha_sign_index": nav_sign,
            "navamsha_sign": SIGNS_TR[nav_sign],
            "navamsha_sign_en": SIGNS_EN[nav_sign],
            "navamsha_degree": nav_degree,
            "navamsha_degree_str": dms_str(nav_degree),
        })

    # Ketu = Rahu + 180°
    rahu_data = [p for p in planet_data if p["abbr"] == "Ra"][0]
    ketu_lon = (rahu_data["longitude"] + 180.0) % 360.0
    ketu_sign_idx = get_sign_index(ketu_lon)
    ketu_degree = get_sign_degree(ketu_lon)
    ketu_nak = get_nakshatra(ketu_lon)
    ketu_nav_sign, ketu_nav_degree = get_navamsha_sign(ketu_lon)
    ketu_house = ((ketu_sign_idx - asc_sign_idx) % 12) + 1

    planet_data.append({
        "id": -1,
        "name": "Ketu",
        "abbr": "Ke",
        "longitude": ketu_lon,
        "sign_index": ketu_sign_idx,
        "sign": SIGNS_TR[ketu_sign_idx],
        "sign_en": SIGNS_EN[ketu_sign_idx],
        "degree": ketu_degree,
        "degree_str": dms_str(ketu_degree),
        "retrograde": True,
        "speed": rahu_data["speed"],
        "house": ketu_house,
        "nakshatra": ketu_nak,
        "navamsha_sign_index": ketu_nav_sign,
        "navamsha_sign": SIGNS_TR[ketu_nav_sign],
        "navamsha_sign_en": SIGNS_EN[ketu_nav_sign],
        "navamsha_degree": ketu_nav_degree,
        "navamsha_degree_str": dms_str(ketu_nav_degree),
    })

    # Vimshottari Dasha
    moon_data = [p for p in planet_data if p["abbr"] == "Mo"][0]
    dashas = calc_vimshottari_dasha(moon_data["longitude"], jd)

    # Navamsha Lagna
    nav_lagna_sign, nav_lagna_degree = get_navamsha_sign(asc_longitude)

    result = {
        "birth_info": {
            "date": f"{day:02d}.{month:02d}.{year}",
            "time": f"{hour:02d}:{minute:02d}:{second:02d}",
            "second": second,
            "timezone": f"UTC{'+' if tz_offset >= 0 else ''}{tz_offset:g}",
            "latitude": lat,
            "longitude_geo": lon
        },
        "ayanamsa": {
            "type": "Lahiri",
            "value": round(swe.get_ayanamsa_ut(jd), 4)
        },
        "lagna": lagna_info,
        "navamsha_lagna": {
            "sign_index": nav_lagna_sign,
            "sign": SIGNS_TR[nav_lagna_sign],
            "sign_en": SIGNS_EN[nav_lagna_sign],
            "degree": nav_lagna_degree,
            "degree_str": dms_str(nav_lagna_degree),
        },
        "planets": planet_data,
        "vimshottari_dasha": dashas[:20],
    }

    return result
