"""Ucretli katman icin kisiye ozel durum paketi.

digest/situation.py'den farkli: Ay burcu kovasi degil, gercek v2 chart
JSON'undan (lordships, planets, houses, dashas) okur. Ayni haritaya
sahip iki kullanici olamayacagi icin donem_alan_sahipligi/
donem_bulundugu_alan/guc gercekten kisiye ozeldir.

DASHA LORDU ARTIK DISARIDAN ALINMAZ. Ilk surumde caller "Jupiter",
"Saturn" gibi elle veriyordu; bu, yanlis lord verilirse sessizce yanlis
uretim riski tasiyordu. Simdi chart['dashas']['vimshottari']
['current_active'] okunuyor (app.py:_v2_dashas, satir ~8133). Bu alan
'active' (dogum ani) DEGIL; reference_dt_utc'ye gore hesaplanir ve v2
chart route'u bu referansi transit_reference'tan (varsayilan: simdi)
gecirir. Kod kaynagindan dogrulandi; ornek JSON dosyasi (statik,
1990 dogum ani) uzerinde 'current_active' ayrica calistirilmadi --
canli /api/v2/chart/full cagrisinda mutlaka kontrol edilmeli.

ana_tema/gun_kalitesi/sade_sati/burc_degisimi icin kendi mantigini
YAZMAZ; situation.build_situation()'i cagirir.

Bu dosya hicbir mevcut dosyayi degistirmez, hicbir route'a baglanmaz.
Yalniz saf fonksiyon icerir; DB, dosya, ag erisimi yoktur.

Girdi:
    chart : _build_v2_chart() ciktisi (veya chart_summary esdegeri).
        chart['dashas']['vimshottari']['current_active'] sart.
    katman: "daily" | "weekly" | "monthly"
    snaps : situation.required_days(katman, d) ile ayni uzunlukta,
        situation.planet_signs() ciktilarindan olusan liste.

Cikti: METODOLOJI_DIGEST.md'nin bekledigi alanlar. Alan yoksa sozluge
hic konulmaz; "veri eksik" gibi bir deger asla yazilmaz.
"""

from .keys import GENERATOR_VERSION, LAYER_DASHA_LEVEL, SNAPSHOT_HOUR
from .rules import house_of
from .writer import HOUSE_THEME
from .situation import build_situation

_STRONG_DIGNITY = ("uccha", "moolatrikona", "swakshetra")
_WEAK_DIGNITY_ESSENTIAL = ("enemy",)

HOMEPAGE_CONTEXT_VERSION = "homepage_digest_context_v1"
HOMEPAGE_METHODOLOGY_VERSION = "digest-methodology-v2"


def _find_planet(chart, planet_name):
    """chart['planets'] icinden isme gore gezegen kaydini bulur."""
    target = str(planet_name or "").strip().lower()
    for p in chart.get("planets", []):
        if str(p.get("name", "")).strip().lower() == target:
            return p
    return None


def _natal_moon_sign_index(chart):
    moon = _find_planet(chart, "Moon")
    if moon is None:
        return None
    idx = moon.get("sign_index")
    return int(idx) if idx is not None else None


def _current_dasha_lord(chart, katman):
    """Katmanin ihtiyac duydugu Vimshottari seviyesinin GUNCEL lordu.

    daily -> None (mevcut tasarimda gunluk katmanda dasha yan parcasi yok).
    weekly -> pratyantar, monthly -> antara (digest/keys.py ile ayni esleme).

    current_active yoksa veya seviye eksikse None doner; caller bu
    durumda dasha baglamini pakete eklemez (uydurma yok).
    """
    level = LAYER_DASHA_LEVEL.get(katman)
    if level is None:
        return None
    current_active = (
        (chart.get("dashas") or {})
        .get("vimshottari", {})
        .get("current_active", {})
    )
    period = current_active.get(level) or {}
    lord = period.get("lord")
    return str(lord) if lord else None


def _guc(planet):
    """Basit 3 seviyeli guc etiketi. Tam shadbala degil; sonradan
    degistirilebilir. uccha/moolatrikona/swakshetra -> guclu,
    neecha/dusman -> zayif, aksi -> orta. Kombust ise bir kademe duser."""
    dign = planet.get("dignity", {}) or {}
    combust = bool((planet.get("combustion") or {}).get("is_combust"))

    if any(dign.get(k) for k in _STRONG_DIGNITY):
        seviye = "guclu"
    elif dign.get("neecha") or dign.get("essential") in _WEAK_DIGNITY_ESSENTIAL:
        seviye = "zayif"
    else:
        seviye = "orta"

    if combust:
        if seviye == "guclu":
            seviye = "orta"
        elif seviye == "orta":
            seviye = "zayif"

    return seviye


def _ruled_houses(chart, dasha_lord):
    """dasha_lord'un dogum haritasinda yonettigi ev(ler). Rahu/Ketu icin
    bos liste doner (bunlar hicbir evi yonetmez)."""
    houses = []
    lordships = chart.get("lordships", {}) or {}
    for house_no_str, entry in lordships.items():
        if str(entry.get("lord", "")).strip().lower() == str(dasha_lord).strip().lower():
            try:
                houses.append(int(house_no_str))
            except (TypeError, ValueError):
                continue
    return sorted(set(houses))


def _theme_join(house_numbers):
    """Bir veya iki ev numarasini HOUSE_THEME uzerinden metne cevirir."""
    themes = [HOUSE_THEME[h] for h in house_numbers if h in HOUSE_THEME]
    if not themes:
        return None
    if len(themes) == 1:
        return themes[0]
    return " ve ".join(themes)


def build_paid_situation(chart, katman, snaps):
    """Kisiye ozel durum paketi. Dasha lordu haritadan otomatik okunur.

    Doner: dict, veya girdi eksikse None.
    """
    natal_moon = _natal_moon_sign_index(chart)
    if natal_moon is None or not snaps:
        return None

    dasha_lord = _current_dasha_lord(chart, katman)
    level = LAYER_DASHA_LEVEL.get(katman)
    taban = build_situation(katman, snaps, natal_moon, dasha_lord, level)

    paket = {"katman": katman}

    # --- ana_tema: situation.py'nin katmana ozel ev hesabindan ---
    ev = house_of(taban)
    if ev in HOUSE_THEME:
        paket["ana_tema"] = HOUSE_THEME[ev]

    # --- gecis_notu: burc degisimi sinyalleri (varsa) ---
    if taban.get("ay_burc_degisimi"):
        paket["gecis_notu"] = "hafta icinde belirgin bir burc gecisi var"
    elif taban.get("gunes_burc_degisimi"):
        paket["gecis_notu"] = "ay icinde belirgin bir burc gecisi var"

    # --- yavaslama_asamasi: yalniz Sade Sati aktifse eklenir ---
    if taban.get("sade_sati"):
        paket["yavaslama_asamasi"] = True

    # --- dasha lord baglami: gercekten kisiye ozel kisim ---
    if dasha_lord:
        lord_planet = _find_planet(chart, dasha_lord)

        ruled = _ruled_houses(chart, dasha_lord)
        tema = _theme_join(ruled)
        if tema:
            paket["donem_alan_sahipligi"] = tema

        if lord_planet is not None:
            lord_house = lord_planet.get("house")
            if lord_house in HOUSE_THEME:
                paket["donem_bulundugu_alan"] = HOUSE_THEME[lord_house]
            paket["guc"] = _guc(lord_planet)

    return paket


def build_homepage_context(chart, d, paketler):
    """Model icin gonderilecek kimliksiz ve surumlu durum paketi.

    Tam chart, dogum bilgisi, koordinat, hesap sahibi veya provider cevabi
    bu sozlugun icine girmez. ``paketler`` yalniz build_paid_situation()
    ciktisidir; chart hash'i ve sahiplik bilgisi route/store katmaninda
    tutulur.
    """
    meta = chart.get("meta", {}) or {}
    missing = []
    if _natal_moon_sign_index(chart) is None:
        missing.append("natal_moon")
    if not (chart.get("dashas") or {}).get("vimshottari", {}).get("current_active"):
        missing.append("current_period")
    for layer in ("daily", "weekly", "monthly"):
        if not paketler.get(layer):
            missing.append(layer)

    return {
        "schema_version": HOMEPAGE_CONTEXT_VERSION,
        "methodology_version": HOMEPAGE_METHODOLOGY_VERSION,
        "local_date": d.isoformat(),
        "calculation": {
            "generator_version": meta.get("engine_version") or GENERATOR_VERSION,
            "snapshot_hour_istanbul": SNAPSHOT_HOUR,
            "source": "verified_chart_and_cached_transit_snapshots",
        },
        "data_quality": {
            "missing": missing,
            "current_period_context_available": "current_period" not in missing,
        },
        "layers": {
            layer: paketler.get(layer) or {}
            for layer in ("daily", "weekly", "monthly")
        },
    }
