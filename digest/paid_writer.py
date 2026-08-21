"""Ucretli katman LLM yazicisi — vedic-vertex-bridge uzerinden.

writer.py'den fark: uc katmani (gunluk/haftalik/aylik) + motto'yu TEK
cagrida uretir; METODOLOJI_DIGEST.md'yi sistem talimati olarak yukler
(digest-methodology-v2, ~1.4 KB — writer.py'nin "8000 sabit token
savunulamaz" gerekcesi burada gecerli degil, cunku gunde bir kez
calisir, katman basina degil).

Donus sozlesmesi writer.py ile ayni: (sonuc, hata_bilgisi).
    sonuc is None      -> caller fallback karar verir (bu modulde
                           kural motoruna otomatik dusme YOK; caller
                           HomeDashboard tarafinda mevcut statik
                           digest'i gostermeye devam eder)
    hata_bilgisi        -> None veya {"asama","exc","fallback_nedeni","sure_ms"}

TEKNIK TERIM SIZINTISI: rules.has_banned() bunu kontrol ETMEZ (yalniz
klise + kesinlik dili). Urunun sabit kurali "hicbir teknik terim
kullanici ciktisina sizmaz" oldugu icin bu dosyada ayri bir tarama var
(_TECHNICAL_LEAK_RE). Bu, mevcut writer.py'de de yok; oradaki tasarim
sabit cumle havuzundan sectigi icin risksiz, burada model serbest
yazdigi icin risk var.
"""

import json
import os
import re
import time
import uuid

MAX_WORDS = {"motto": 20, "gunluk": 50, "haftalik": 50, "aylik": 50}
ALLOWED_FOCUS = {
    "kendin", "kaynak", "girişim", "huzur", "yaratıcılık", "düzen",
    "ilişki", "derinlik", "anlam", "iş", "çevre", "dinlenme",
}
_ID_SAFE = re.compile(r"[^0-9a-zA-Z._:-]")

_METODOLOJI_PATH = os.path.join(os.path.dirname(__file__), "METODOLOJI_DIGEST.md")


def _load_methodology():
    with open(_METODOLOJI_PATH, "r", encoding="utf-8") as f:
        return f.read()


# Modul yuklenirken bir kez okunur; dosya degismedikce tekrar diske
# gidilmez. Deploy sirasinda surec yeniden baslar, guncel icerik gelir.
_METHODOLOGY_TEXT = _load_methodology()

_BANNED_PHRASES = [
    "evren sana", "kozmik enerji", "enerjini yükselt", "şanslı gün",
    "büyük değişim", "hayatın değişecek", "dikkat!",
]
_BANNED_WORDS = [
    "kaçırma", "mutlaka", "kesinlikle", "asla", "tehlike", "uyarı",
]

# Teknik terim sizintisi taramasi. Gezegen/burc adlari hem Turkce hem
# Ingilizce olarak, "N. ev" / "N ev" kalibi, ve genel Vedik terimler.
_PLANETS = [
    "güneş", "gunes", "ay burcu", "mars", "merkür", "merkur", "jüpiter",
    "jupiter", "venüs", "venus", "satürn", "saturn", "rahu", "ketu",
    "sun", "moon", "mercury", "mars ",
]
_SIGNS = [
    "koç", "koc burcu", "boğa", "boga", "i̇kizler", "ikizler", "yengeç",
    "yengec", "aslan burcu", "başak", "basak", "terazi", "akrep",
    "yay burcu", "oğlak", "oglak", "kova burcu", "balık burcu", "balik burcu",
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
    "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]
_TERMS = [
    "nakshatra", "nakshat", "varga", "dasha", "dasa", "yükselen",
    "yukselen", "lagna", "transit", "retro", "gochara", "bhava",
    "rashi", "burç haritası", "burc haritasi",
]
_HOUSE_PATTERN = re.compile(
    r"\b(\d{1,2}\.?\s*(ev|house)|birinci ev|ikinci ev|üçüncü ev|ucuncu ev|"
    r"dördüncü ev|dorduncu ev|beşinci ev|besinci ev|altıncı ev|altinci ev|"
    r"yedinci ev|sekizinci ev|dokuzuncu ev|onuncu ev|on birinci ev|"
    r"on ikinci ev)\b",
    re.IGNORECASE,
)
_IMPERATIVE_RE = re.compile(
    r"\b(?:yap|başla|basla|unutma|bekle|kaçın|kacin|koru|seç|sec|sürdür|surdur|bırak|birak|odaklan|açıl|acil)\b",
    re.IGNORECASE,
)


def _leaks_technical_terms(text):
    low = (text or "").lower()
    for grup in (_PLANETS, _SIGNS, _TERMS):
        for kelime in grup:
            if kelime in low:
                return True
    return bool(_HOUSE_PATTERN.search(low))


def _has_banned(text):
    low = (text or "").lower()
    if any(p in low for p in _BANNED_PHRASES):
        return True
    return any(
        re.search(r"(?<![0-9A-Za-zÇĞİıÖŞÜçğöşü])%s(?![0-9A-Za-zÇĞİıÖŞÜçğöşü])" % re.escape(w), low)
        for w in _BANNED_WORDS
    )


def _has_imperative(text):
    return bool(_IMPERATIVE_RE.search(text or ""))


def llm_enabled():
    return os.getenv("DIGEST_LLM_ENABLED", "0") == "1"


def _safe_request_id():
    raw = "digest-paid-%s" % uuid.uuid4().hex
    return _ID_SAFE.sub("-", raw)[:200]


def _user_text(daily_paket, weekly_paket, monthly_paket, context=None):
    """Uc katmani model icin okunur JSON'a cevirir. Alan yoksa hic
    yazilmaz (paketlerde zaten yok)."""
    gövde = {
        "context_schema": "homepage_digest_context_v1",
        "gunluk": daily_paket or {},
        "haftalik": weekly_paket or {},
        "aylik": monthly_paket or {},
    }
    if context:
        gövde["context"] = context
    return json.dumps(gövde, ensure_ascii=False, indent=2)


def _call_bridge(user_text):
    from vertex_bridge_client import call_vertex_bridge

    request = {
        "systemInstruction": {"parts": [{"text": _METHODOLOGY_TEXT}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "MINIMAL"},
        },
    }
    _, payload = call_vertex_bridge(_safe_request_id(), request)
    return payload


def _response_text(payload):
    parts = payload["candidates"][0]["content"]["parts"]
    text = "".join(
        str(p.get("text") or "") for p in parts if isinstance(p, dict)
    ).strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
    return text


def _word_count(text):
    return len([w for w in str(text).split() if w.strip()])


def validate(payload):
    """Gecerliyse temiz dict, degilse (None, neden)."""
    if not isinstance(payload, dict):
        return None, "json_sozluk_degil"

    motto = payload.get("motto")
    if not isinstance(motto, str) or not motto.strip():
        return None, "motto_bos"
    motto = motto.strip()
    if _word_count(motto) > MAX_WORDS["motto"]:
        return None, "motto_kelime_siniri_asildi"

    temiz = {"motto": motto}

    for katman in ("gunluk", "haftalik", "aylik"):
        blok = payload.get(katman)
        if not isinstance(blok, dict):
            return None, "%s_eksik" % katman
        metin = blok.get("metin")
        odak = blok.get("odak")
        if not isinstance(metin, str) or not metin.strip():
            return None, "%s_metin_bos" % katman
        if not isinstance(odak, str) or not odak.strip():
            return None, "%s_odak_bos" % katman
        metin = metin.strip()
        odak = odak.strip()
        if _word_count(metin) > MAX_WORDS[katman]:
            return None, "%s_kelime_siniri_asildi" % katman
        if len(odak.split()) > 1:
            return None, "%s_odak_tek_kelime_degil" % katman
        if odak.casefold() not in {v.casefold() for v in ALLOWED_FOCUS}:
            return None, "%s_odak_allowlist_disi" % katman
        temiz[katman] = {"metin": metin, "odak": odak}

    tum_metin = " ".join([temiz["motto"]] + [temiz[k]["metin"] for k in ("gunluk", "haftalik", "aylik")])
    if _has_banned(tum_metin):
        return None, "yasakli_ifade"
    if _leaks_technical_terms(tum_metin):
        return None, "teknik_terim_sizintisi"
    if _has_imperative(tum_metin):
        return None, "emir_kipi"
    metinler = [temiz[k]["metin"].casefold() for k in ("gunluk", "haftalik", "aylik")]
    if len(set(metinler)) != len(metinler):
        return None, "tekrarli_katman_metni"

    return temiz, None


def generate(daily_paket, weekly_paket, monthly_paket, context=None):
    """Doner: (sonuc, hata_bilgisi). sonuc None ise caller mevcut
    statik digest'i gostermeye devam etmeli — kural motoruna otomatik
    dusme burada YOK, cunku ucretli akis ayri bir bileşen."""
    if not llm_enabled():
        return None, {"asama": "kapali", "exc": None,
                      "fallback_nedeni": "DIGEST_LLM_ENABLED=0", "sure_ms": 0}

    t0 = time.time()
    user_text = _user_text(daily_paket, weekly_paket, monthly_paket, context)

    try:
        payload = _call_bridge(user_text)
    except Exception as exc:
        return None, {"asama": "bridge", "exc": exc,
                      "fallback_nedeni": "bridge_cagrisi_basarisiz",
                      "sure_ms": int((time.time() - t0) * 1000)}

    try:
        raw = json.loads(_response_text(payload))
    except Exception as exc:
        return None, {"asama": "parse", "exc": exc,
                      "fallback_nedeni": "yanit_ayristirilamadi",
                      "sure_ms": int((time.time() - t0) * 1000)}

    sonuc, neden = validate(raw)
    sure = int((time.time() - t0) * 1000)
    if sonuc is None:
        return None, {"asama": "validate", "exc": None,
                      "fallback_nedeni": neden, "sure_ms": sure}
    sonuc["sure_ms"] = sure
    return sonuc, None
