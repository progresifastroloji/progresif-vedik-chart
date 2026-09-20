"""Yedi günlük kişisel ana sayfa yorumu için tek çağrılık yazıcı.

Chart API gün bazlı kanıtı seçer; bu modül yalnız kullanıcıya gösterilecek
kısa anlatıyı üretir ve sıkı biçimde denetler. Model hesap yapmaz, teknik
terim veya kanıt paketinde olmayan yaşam alanı ekleyemez.
"""

import json
import os
import re
import time
import uuid

MAX_WORDS = {"motto": 20, "yorum": 110, "derin_yorum": 180}
MIN_WORDS = {"yorum": 32, "derin_yorum": 90}
ALLOWED_FOCUS = {
    "kendin", "kaynak", "girişim", "huzur", "yaratıcılık", "düzen",
    "ilişki", "derinlik", "anlam", "iş", "çevre", "dinlenme",
}
ENGLISH_ALLOWED_FOCUS = {
    "self", "resources", "initiative", "peace", "creativity", "structure",
    "relationships", "depth", "meaning", "work", "community", "rest",
}
FOCUS_TRANSLATIONS = {
    "kendin": "self", "kaynak": "resources", "girişim": "initiative",
    "huzur": "peace", "yaratıcılık": "creativity", "düzen": "structure",
    "ilişki": "relationships", "derinlik": "depth", "anlam": "meaning",
    "iş": "work", "çevre": "community", "dinlenme": "rest",
}
FOCUS_TERMS = {
    "kendin": ("kendin", "sınır", "duruş", "istek", "ifade"),
    "kaynak": ("kaynak", "para", "birikim", "güven", "söz"),
    "girişim": ("adım", "iletişim", "yakın çevre", "hareket", "başlat"),
    "huzur": ("ev", "iç dünya", "sakin", "yuva", "huzur"),
    "yaratıcılık": ("fikir", "keyif", "yarat", "ifade", "gönül"),
    "düzen": ("rutin", "iş yük", "program", "düzen", "sorumluluk"),
    "ilişki": ("ilişki", "karşı taraf", "ortak", "bağ", "yakınlık"),
    "derinlik": ("gizli", "paylaş", "belirsiz", "derin", "mahrem"),
    "anlam": ("öğren", "inanç", "bakış", "ufuk", "anlam"),
    "iş": ("iş", "çalış", "kariyer", "görev", "sorumluluk"),
    "çevre": ("arkadaş", "çevre", "bağlantı", "topluluk", "destek"),
    "dinlenme": ("dinlen", "mola", "yavaş", "sessiz", "toparlan"),
}
ENGLISH_FOCUS_TERMS = {
    "self": ("yourself", "boundary", "identity", "voice"),
    "resources": ("resources", "money", "security", "savings"),
    "initiative": ("step", "communication", "movement", "start"),
    "peace": ("home", "calm", "inner life", "settle"),
    "creativity": ("idea", "creative", "joy", "expression"),
    "structure": ("routine", "schedule", "workload", "structure"),
    "relationships": ("relationship", "partner", "other person", "bond"),
    "depth": ("private", "shared", "uncertainty", "depth"),
    "meaning": ("learning", "belief", "meaning", "horizon"),
    "work": ("work", "career", "task", "responsibility"),
    "community": ("friend", "community", "connection", "support"),
    "rest": ("rest", "pause", "quiet", "recover"),
}
ALLOWED_DOMAINS = {"love", "work", "family", "friends"}
_ID_SAFE = re.compile(r"[^0-9a-zA-Z._:-]")
_METODOLOJI_PATH = os.path.join(os.path.dirname(__file__), "METODOLOJI_DIGEST.md")

_BANNED_PHRASES = ("evren sana", "kozmik enerji", "enerjini yükselt", "şanslı gün", "büyük değişim", "hayatın değişecek", "dikkat!", "kaderinde")
_BANNED_WORDS = ("mutlaka", "kesinlikle", "asla", "tehlike", "uyarı", "garanti")
_ENGLISH_BANNED_PHRASES = ("the universe", "cosmic energy", "raise your energy", "lucky day", "big change", "your life will change", "it is destined")
_ENGLISH_BANNED_WORDS = ("must", "definitely", "never", "danger", "warning", "guarantee")
_FUTURE_CLAIM_RE = re.compile(r"\b(?:olacak(?:sın|tır)?|gelecek|gerçekleşecek|kesinleşecek|evleneceksin|ayrılacaksın|kazanacaksın|kaybedeceksin)\b", re.IGNORECASE)
_ENGLISH_FUTURE_CLAIM_RE = re.compile(r"\b(?:will happen|will definitely|is guaranteed|you will marry|you will lose|you will gain)\b", re.IGNORECASE)
_PLANETS = ("güneş", "gunes", "ay burcu", "mars", "merkür", "merkur", "jüpiter", "jupiter", "venüs", "venus", "satürn", "saturn", "rahu", "ketu", "sun", "moon", "mercury")
_SIGNS = ("koç", "koc burcu", "boğa", "boga", "i̇kizler", "ikizler", "yengeç", "yengec", "aslan burcu", "başak", "basak", "terazi", "akrep", "yay burcu", "oğlak", "oglak", "kova burcu", "balık burcu", "balik burcu", "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces")
_TERMS = ("nakshatra", "varga", "dasha", "dasa", "yükselen", "yukselen", "lagna", "transit", "retro", "gochara", "bhava", "rashi", "burç haritası", "burc haritasi", "panchanga", "tithi")
_HOUSE_PATTERN = re.compile(r"\b(?:\d{1,2}\.?\s*(?:ev|house)|birinci ev|ikinci ev|üçüncü ev|ucuncu ev|dördüncü ev|dorduncu ev|beşinci ev|besinci ev|altıncı ev|altinci ev|yedinci ev|sekizinci ev|dokuzuncu ev|onuncu ev|on birinci ev|on ikinci ev)\b", re.IGNORECASE)
_TECHNICAL_TERM_PATTERN = re.compile(
    r"(?<![0-9A-Za-zÇĞİıÖŞÜçğöşü])(?:%s)(?![0-9A-Za-zÇĞİıÖŞÜçğöşü])" %
    "|".join(re.escape(term) for term in (*_PLANETS, *_SIGNS, *_TERMS)),
    re.IGNORECASE,
)


def _load_methodology():
    with open(_METODOLOJI_PATH, "r", encoding="utf-8") as file:
        return file.read()


_METHODOLOGY_TEXT = _load_methodology()


def llm_enabled():
    return os.getenv("DIGEST_LLM_ENABLED", "0") == "1"


def _safe_request_id():
    return _ID_SAFE.sub("-", "digest-week-%s" % uuid.uuid4().hex)[:200]


def _word_count(text):
    return len([word for word in str(text).split() if word.strip()])


def _leaks_technical_terms(text):
    lowered = (text or "").lower()
    return bool(_TECHNICAL_TERM_PATTERN.search(lowered)) or bool(_HOUSE_PATTERN.search(lowered))


def _has_banned(text, language):
    lowered = (text or "").lower()
    phrases = _ENGLISH_BANNED_PHRASES if language == "en" else _BANNED_PHRASES
    words = _ENGLISH_BANNED_WORDS if language == "en" else _BANNED_WORDS
    return any(phrase in lowered for phrase in phrases) or any(re.search(r"(?<![0-9A-Za-zÇĞİıÖŞÜçğöşü])%s(?![0-9A-Za-zÇĞİıÖŞÜçğöşü])" % re.escape(word), lowered) for word in words)


def _has_future_claim(text, language):
    return bool((_ENGLISH_FUTURE_CLAIM_RE if language == "en" else _FUTURE_CLAIM_RE).search(text or ""))


def _reflects_focus(text, focus, language):
    terms = ENGLISH_FOCUS_TERMS if language == "en" else FOCUS_TERMS
    return any(term.casefold() in (text or "").casefold() for term in terms.get(focus.casefold(), ()))


def _response_text(payload):
    parts = payload["candidates"][0]["content"]["parts"]
    text = "".join(str(part.get("text") or "") for part in parts if isinstance(part, dict)).strip()
    if text.startswith("```json") and text.endswith("```"):
        return text[7:-3].strip()
    if text.startswith("```") and text.endswith("```"):
        return text[3:-3].strip()
    return text


def _user_text(context, language):
    week = context
    if language == "en":
        def english_day(day):
            focus = FOCUS_TRANSLATIONS.get(str(day.get("focus") or "").casefold(), day.get("focus"))
            return {**day, "focus": focus, "focus_anchors": ENGLISH_FOCUS_TERMS.get(focus, ())}

        week = {**context, "days": [english_day(day) for day in context.get("days", [])]}
        instruction = (
            "Return natural English only. Copy each given focus exactly into odak. Each day must contain one coherent paragraph of 32 to 110 words. "
            "Include at least one supplied focus_anchors phrase verbatim in the paragraph, but do not output focus_anchors. "
            "First identify the day's emphasis, then explain its personal meaning, then offer calm practical guidance. "
            "Never state a future outcome as certain or guaranteed. Avoid phrases such as will happen, will definitely, is certain to, "
            "or promises about relationships, work, money, health, or other people. Use conditional language such as may, can, or consider instead."
        )
    else:
        week = {**context, "days": [
            {**day, "focus_anchors": FOCUS_TERMS.get(str(day.get("focus") or "").casefold(), ())}
            for day in context.get("days", [])
        ]}
        instruction = (
            "Kullanıcıya gösterilecek bütün değerleri doğal Türkiye Türkçesiyle yaz. Her odak değerini kanıttan aynen kopyala. "
            "Her gün için 32 ile 110 kelime arasında tek, akıcı paragraf yaz ve focus_anchors listesindeki en az bir ifadeyi paragrafta aynen kullan; "
            "focus_anchors listesini çıktıya koyma. Paragraf önce günün tespitini, sonra bunun kişisel anlamını, ardından sakin ve uygulanabilir rehberliği taşısın. "
            "Geleceğe dair kesinlik, garanti veya vaat kurma. Olacak, kesinleşecek, mutlaka, kesin, garanti, kaderinde var gibi ifadeleri kullanma; "
            "olabilir, öne çıkabilir, fark edebilirsin, değerlendirebilirsin gibi koşullu ve özgür iradeyi koruyan dil kullan."
        )
    return json.dumps({"context_schema": "homepage_digest_context_v4", "week": week, "output_language": "English" if language == "en" else "Turkish", "output_instruction": instruction}, ensure_ascii=False, indent=2)


def _deep_user_text(day, language):
    instruction = (
        "Return natural English only. Write one deeper, coherent paragraph of 90 to 180 words for this day. "
        "Develop the supplied focus into a more nuanced personal interpretation and practical guidance. Do not introduce facts outside the supplied evidence. "
        "Never state a future outcome as certain or guaranteed; use conditional, choice-preserving language instead."
        if language == "en" else
        "Yalnız doğal Türkiye Türkçesi kullan. Bu gün için 90 ile 180 kelime arasında tek, daha derin ve akıcı bir paragraf yaz. "
        "Verilen odağı daha incelikli kişisel yorum ve uygulanabilir rehberlikle geliştir. Sağlanan kanıtın dışına çıkma. "
        "Gelecek hakkında kesinlik, garanti veya vaat kurma; koşullu, seçimi kullanıcıda bırakan bir dil kullan."
    )
    return json.dumps({"context_schema": "homepage_digest_deep_context_v1", "day": day, "output_language": "English" if language == "en" else "Turkish", "output_instruction": instruction}, ensure_ascii=False, indent=2)


def _call_bridge(user_text, language):
    from vertex_bridge_client import call_vertex_bridge
    language_instruction = "Return natural English only. Do not use Turkish words or suffixes." if language == "en" else "Yalnız doğal Türkiye Türkçesi kullan."
    request = {"systemInstruction": {"parts": [{"text": _METHODOLOGY_TEXT + "\n\n" + language_instruction}]}, "contents": [{"role": "user", "parts": [{"text": user_text}]}], "generationConfig": {"temperature": 0.4 if language == "tr" else 0.65, "maxOutputTokens": 3072, "responseMimeType": "application/json", "thinkingConfig": {"thinkingLevel": "MINIMAL"}}}
    _, payload = call_vertex_bridge(_safe_request_id(), request)
    return payload


def validate(payload, context, language="tr"):
    """Yalnız yedi beklenen gün ve kanıtla izinli alanları kabul eder."""
    if not isinstance(payload, dict):
        return None, "json_sozluk_degil"
    motto, days = payload.get("motto"), payload.get("days")
    if not isinstance(motto, str) or not motto.strip():
        return None, "motto_bos"
    if _word_count(motto) > MAX_WORDS["motto"]:
        return None, "motto_kelime_siniri_asildi"
    if not isinstance(days, list) or len(days) != 7:
        return None, "yedi_gun_gerekli"
    expected = context.get("days") if isinstance(context, dict) else None
    if not isinstance(expected, list) or len(expected) != 7:
        return None, "kanit_yedi_gun_degil"
    expected_by_date = {str(day.get("date")): day for day in expected if isinstance(day, dict)}
    if len(expected_by_date) != 7:
        return None, "kanit_tarihleri_gecersiz"
    allowed_focus = ENGLISH_ALLOWED_FOCUS if language == "en" else ALLOWED_FOCUS
    cleaned_days, seen_dates, seen_messages = [], set(), set()
    for card in days:
        if not isinstance(card, dict):
            return None, "gun_karti_sozluk_degil"
        date = str(card.get("date") or "").strip()
        evidence = expected_by_date.get(date)
        if not evidence or date in seen_dates:
            return None, "gun_tarihi_kanitla_uyusmuyor"
        seen_dates.add(date)
        focus = str(card.get("odak") or "").strip()
        expected_focus = str(evidence.get("focus") or "").strip()
        if language == "en":
            expected_focus = FOCUS_TRANSLATIONS.get(expected_focus.casefold(), expected_focus)
        if focus.casefold() not in {value.casefold() for value in allowed_focus} or focus.casefold() != expected_focus.casefold():
            return None, "gun_odagi_kanitla_uyusmuyor"
        cleaned = {"date": date, "odak": focus}
        yorum = card.get("yorum")
        if not isinstance(yorum, str) or not yorum.strip():
            return None, "yorum_bos"
        yorum = yorum.strip()
        if _word_count(yorum) < MIN_WORDS["yorum"] or _word_count(yorum) > MAX_WORDS["yorum"]:
            return None, "yorum_kelime_siniri"
        cleaned["yorum"] = yorum
        domains = card.get("alanlar", [])
        if not isinstance(domains, list) or any(not isinstance(item, str) for item in domains):
            return None, "alanlar_gecersiz"
        domains = [item.strip().lower() for item in domains if item.strip()]
        if len(domains) != len(set(domains)) or any(item not in ALLOWED_DOMAINS for item in domains):
            return None, "alanlar_gecersiz"
        if not set(domains).issubset(set(evidence.get("eligible_domains") or [])):
            return None, "alan_kanitla_uyusmuyor"
        cleaned["alanlar"] = domains
        if not _reflects_focus(yorum, focus, language):
            return None, "gun_metni_odakla_uyusmuyor"
        marker = yorum.casefold()
        if marker in seen_messages:
            return None, "tekrarli_yorum"
        seen_messages.add(marker)
        cleaned_days.append(cleaned)
    if set(seen_dates) != set(expected_by_date):
        return None, "gun_tarihleri_eksik"
    all_text = " ".join([motto.strip()] + [card["yorum"] for card in cleaned_days])
    if _has_banned(all_text, language):
        return None, "yasakli_ifade"
    if _has_future_claim(all_text, language):
        return None, "kesin_gelecek_iddiasi"
    if _leaks_technical_terms(all_text):
        return None, "teknik_terim_sizintisi"
    return {"motto": motto.strip(), "days": cleaned_days}, None


def validate_deep(payload, day, language="tr"):
    """Premium ayrıntının yalnız seçilen günün kanıtına bağlı kalmasını sağlar."""
    if not isinstance(payload, dict):
        return None, "json_sozluk_degil"
    yorum = payload.get("yorum")
    if not isinstance(yorum, str) or not yorum.strip():
        return None, "derin_yorum_bos"
    yorum = yorum.strip()
    if _word_count(yorum) < MIN_WORDS["derin_yorum"] or _word_count(yorum) > MAX_WORDS["derin_yorum"]:
        return None, "derin_yorum_kelime_siniri"
    focus = str((day or {}).get("focus") or "").strip()
    if not focus:
        return None, "gun_odagi_yok"
    if language == "en":
        focus = FOCUS_TRANSLATIONS.get(focus.casefold(), focus)
    if not _reflects_focus(yorum, focus, language):
        return None, "derin_yorum_odakla_uyusmuyor"
    if _has_banned(yorum, language):
        return None, "yasakli_ifade"
    if _has_future_claim(yorum, language):
        return None, "kesin_gelecek_iddiasi"
    if _leaks_technical_terms(yorum):
        return None, "teknik_terim_sizintisi"
    return yorum, None


def generate(context, language="tr"):
    if not llm_enabled():
        return None, {"asama": "kapali", "fallback_nedeni": "DIGEST_LLM_ENABLED=0", "sure_ms": 0}
    started = time.time()
    try:
        payload = _call_bridge(_user_text(context, language), language)
    except Exception as exc:
        return None, {"asama": "bridge", "exc": exc, "fallback_nedeni": "bridge_cagrisi_basarisiz", "sure_ms": int((time.time() - started) * 1000)}
    try:
        raw = json.loads(_response_text(payload))
    except Exception as exc:
        return None, {"asama": "parse", "exc": exc, "fallback_nedeni": "yanit_ayristirilamadi", "sure_ms": int((time.time() - started) * 1000)}
    result, reason = validate(raw, context, language)
    elapsed = int((time.time() - started) * 1000)
    if result is None:
        return None, {"asama": "validate", "fallback_nedeni": reason, "sure_ms": elapsed}
    result["sure_ms"] = elapsed
    return result, None


def generate_deep(day, language="tr"):
    if not llm_enabled():
        return None, {"asama": "kapali", "fallback_nedeni": "DIGEST_LLM_ENABLED=0", "sure_ms": 0}
    started = time.time()
    try:
        payload = _call_bridge(_deep_user_text(day, language), language)
    except Exception as exc:
        return None, {"asama": "bridge", "exc": exc, "fallback_nedeni": "bridge_cagrisi_basarisiz", "sure_ms": int((time.time() - started) * 1000)}
    try:
        raw = json.loads(_response_text(payload))
    except Exception as exc:
        return None, {"asama": "parse", "exc": exc, "fallback_nedeni": "yanit_ayristirilamadi", "sure_ms": int((time.time() - started) * 1000)}
    result, reason = validate_deep(raw, day, language)
    elapsed = int((time.time() - started) * 1000)
    if result is None:
        return None, {"asama": "validate", "fallback_nedeni": reason, "sure_ms": elapsed}
    return result, {"sure_ms": elapsed}
