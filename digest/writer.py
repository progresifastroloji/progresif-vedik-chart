"""LLM metin katmani — vedic-vertex-bridge uzerinden.

Varsayilan KAPALI (DIGEST_LLM_ENABLED=0).

Donus sozlesmesi: (sonuc, hata_bilgisi)
    sonuc is None  -> kural motoruna dusulur
    hata_bilgisi   -> None veya {"asama","exc","fallback_nedeni","sure_ms"}

Sessiz fallback yoktur; her basarisizligin nedeni cagirana bildirilir.

Metodoloji dosyasi BU KATMANDA YUKLENMEZ. Gunluk tek cumle icin
8.000 sabit token savunulamaz.

Bridge sozlesmesi methodology_orchestrator._model_request ile ayni.
"""

import json
import os
import re
import time
import uuid

from .rules import has_banned, house_of

_ID_SAFE = re.compile(r"[^0-9a-zA-Z._:-]")

MAX_WORDS = 22


def llm_enabled():
    return os.getenv("DIGEST_LLM_ENABLED", "0") == "1"


_ORTAK_KURALLAR = """KESIN KURALLAR
- Tek cumle. Maksimum 22 kelime.
- Yumusak kip zorunlu: "olabilir", "gelebilir", "one cikabilir".
- Emir kipi kullanma.
- Astroloji terimi kullanma: gezegen adi, burc adi, ev numarasi,
  nakshatra, donem adi, varga, dasha, yukselen.
- Kesin yargi, kader dili, korkutma yok.
- Tibbi, hukuki, finansal kesinlik yok.
- Su ifadeleri kullanma: evren sana, kozmik enerji, sansli gun,
  kacirma, buyuk degisim, hayatin degisecek, mutlaka, kesinlikle.
- Duzgun Turkiye Turkcesi kullan.

CIKTI: yalnizca JSON.
{"cumle": "...", "odak": "<tek kelime>"}"""

_ROL = "ROL: Vedik astroloji yorumunu sade Turkceye ceviren yazar.\n"

PROMPTS = {
    "daily": (
        _ROL
        + "GOREV: Verilen duruma karsilik BUGUNE dair tek cumle uret.\n"
        + 'Cumle "Bugun" kelimesiyle BASLAMASIN.\n\n'
        + _ORTAK_KURALLAR
    ),
    "weekly": (
        _ROL
        + "GOREV: Verilen duruma karsilik BU HAFTAYA dair tek cumle uret.\n"
        + 'Cumle "Bu hafta" ile baslayabilir. Iki bolum arasinda tek bir\n'
        + "noktali virgul kullan.\n\n"
        + _ORTAK_KURALLAR
    ),
    "monthly": (
        _ROL
        + "GOREV: Verilen duruma karsilik BU AYA dair tek cumle uret.\n"
        + 'Cumle "Bu ay" ile baslayabilir. Ton yavas ve donemsel olsun.\n'
        + "Iki bolum arasinda tek bir noktali virgul kullan.\n\n"
        + _ORTAK_KURALLAR
    ),
}

HOUSE_THEME = {
    1: "kisinin kendisi, gorunurluk, kendini ifade",
    2: "kaynaklar, birikim, aile ici, soz",
    3: "girisim, cesaret, kisa temaslar, yakin cevre",
    4: "ev, huzur, ic dunya, yerlesiklik",
    5: "yaraticilik, keyif, gonul isleri, zihin",
    6: "is yuku, duzen, dayaniklilik, rutin",
    7: "iliski, ortaklik, karsi taraf, anlasma",
    8: "derinlik, gizli konular, paylasilan kaynaklar",
    9: "anlam, inanc, ogrenme, uzak konular",
    10: "is, statu, sorumluluk, gorunurluk",
    11: "kazanc, hedef, cevre destegi, baglanti",
    12: "geri cekilme, dinlenme, yavaslama",
}

# Dasha yan parcasi modele tema olarak verilir; gezegen adi gitmez.
DASHA_THEME = {
    "Ketu": "sadelesme ve geri cekilme",
    "Venus": "uyum ve yakinlasma",
    "Sun": "one cikma ve kendi yonunu belirleme",
    "Moon": "duygusal yakinlik ve bakim",
    "Mars": "atilim ve hareket",
    "Rahu": "yenilik ve disari acilma",
    "Jupiter": "genisleme ve anlam arayisi",
    "Saturn": "sorumluluk ve sabir",
    "Mercury": "iletisim ve ogrenme",
}


def _safe_request_id(layer):
    raw = "digest-%s-%s" % (layer or "x", uuid.uuid4().hex)
    return _ID_SAFE.sub("-", raw)[:200]


def _user_text(situation):
    house = house_of(situation)
    satirlar = [
        "DURUM",
        "- Tema: %s" % HOUSE_THEME[house],
        "- Genel ton: %s" % situation.get("gun_kalitesi", "notr"),
    ]

    lord = situation.get("dasha_lord")
    if lord and lord in DASHA_THEME:
        satirlar.append("- Donem vurgusu: %s" % DASHA_THEME[lord])

    if situation.get("sade_sati"):
        satirlar.append(
            "- Ek not: yavaslik ve sorumluluk asamasi. Korkutucu dil "
            "kullanma; vurgu sabir ve kalicilik uzerine olsun.")

    if situation.get("ay_burc_degisimi"):
        satirlar.append("- Not: hafta icinde belirgin bir gecis var.")
    if situation.get("gunes_burc_degisimi"):
        satirlar.append("- Not: ay icinde belirgin bir gecis var.")

    satirlar += ["", "Bu duruma karsilik tek cumle uret."]
    return "\n".join(satirlar)


def _call_bridge(situation):
    from vertex_bridge_client import call_vertex_bridge

    layer = situation["layer"]
    request = {
        "systemInstruction": {"parts": [{"text": PROMPTS[layer]}]},
        "contents": [{"role": "user", "parts": [{"text": _user_text(situation)}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 256,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "MINIMAL"},
        },
    }
    _, payload = call_vertex_bridge(_safe_request_id(layer), request)
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


def validate(payload, layer):
    """Gecerliyse sozluk, degilse (None, neden) icin neden metni doner."""
    if not isinstance(payload, dict):
        return None, "json_sozluk_degil"
    cumle = payload.get("cumle")
    odak = payload.get("odak")
    if not isinstance(cumle, str) or not cumle.strip():
        return None, "cumle_bos"
    if not isinstance(odak, str) or not odak.strip():
        return None, "odak_bos"
    cumle = cumle.strip()
    odak = odak.strip()
    if _word_count(cumle) > MAX_WORDS:
        return None, "kelime_siniri_asildi"
    if has_banned(cumle):
        return None, "yasakli_ifade"
    if len(odak.split()) > 1:
        return None, "odak_tek_kelime_degil"
    if cumle.count(";") > 1:
        return None, "coklu_noktali_virgul"
    if layer == "daily" and cumle.lower().startswith("bugün"):
        return None, "bugun_ile_basliyor"
    return {"cumle": cumle, "odak": odak}, None


def generate(situation):
    """Doner: (sonuc, hata_bilgisi). sonuc None ise kural motoruna dusulur."""
    if not llm_enabled():
        return None, None  # kapali olmak hata degildir

    layer = situation.get("layer")
    if layer not in PROMPTS:
        return None, {"asama": "prompt", "exc": None,
                      "fallback_nedeni": "bilinmeyen_katman", "sure_ms": 0}

    t0 = time.time()
    try:
        payload = _call_bridge(situation)
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

    sonuc, neden = validate(raw, layer)
    sure = int((time.time() - t0) * 1000)
    if sonuc is None:
        return None, {"asama": "validate", "exc": None,
                      "fallback_nedeni": neden, "sure_ms": sure}
    sonuc["sure_ms"] = sure
    return sonuc, None
