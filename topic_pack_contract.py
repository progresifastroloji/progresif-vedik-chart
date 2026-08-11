# -*- coding: utf-8 -*-
"""
Konu paketi sozlesmesi ve veri kapisi bloklari.

Kaynak: PJRC v11.12 / 05-Phase5-Roadmap / P01-P11 Profesyonel Paketler (ACTIVE v3.3.0)
Kural kunyeleri: RUL-PH5-*-01/02/03, RUL-PH3-0008, RUL-T05-0001

Bu modul hesap yapmaz. Yalniz chart sozlugundeki mevcut alanlari okur ve
markdown blok uretir. app.py icindeki hicbir mevcut davranisi degistirmez.
"""

VERSION = "1.1.0"


# --------------------------------------------------------------------------
# Kanonik konu paketi kaydi
# --------------------------------------------------------------------------

TOPIC_PACK_REGISTRY = {
    "P01-REL": {
        "name": "Romantik İlişki",
        "category": "Romantic attachment, relationship pattern, boundary and communication",
        "excluded": ["formal marriage decision", "business partnership", "legal outcome"],
        "surfaces": [
            "Lagna/Lagna lord", "5. ev/lord", "7. ev/lord", "Venüs", "Ay",
            "Mars", "Güneş", "dispozitörler", "drishtiler", "karşı kanıt",
        ],
        "varga_required": ["D9"],
        "varga_support": ["D30"],
        "varga_note": "D30 yalniz catisma/stres bağlaminda ve veri kapisi acikken",
        "timing": "Vimśottarī erişim | ilişki penceresi | hızlı tetik | hazır oluş",
        "jaimini": "DK, A7, UL yalnız paralel karşılaştırma",
        "counter_focus": "5./7. ev ağı çelişkisi, Venüs/Ay/Mars çelişkisi, bağlanma uyumsuzluğu",
        "allowed": [
            "ilişki örüntüsü", "çekim ve bağlanma mekanizması",
            "sınır ve iletişim koşulları", "geniş zaman penceresi",
        ],
        "blocked": [
            "partner zihin okuma", "garanti birleşme",
            "aldatma kesinliği", "kesin ayrılık tarihi",
        ],
        "context_questions": [
            "Mevcut ilişki durumu?", "Beklenti ve zaman ufku?",
            "Kültür ve aile bağlamı?",
        ],
        "risk_level": "R1-CONTEXT",
        "production_status": "CORE-WITH-SAFETY",
        "human_review": False,
    },
    "P01-MAR": {
        "name": "Evlilik ve Resmî Birliktelik",
        "category": "Commitment capacity, durability, formalization of union",
        "excluded": ["romantic attraction only", "business partnership", "divorce litigation"],
        "surfaces": [
            "Lagna/Lagna lord", "7. ev/lord", "2. ev/lord", "Venüs", "Jüpiter",
            "Ay", "Mars", "Güneş", "dayaniklilik/karşı kanıt",
        ],
        "varga_required": ["D9"],
        "varga_support": ["D2", "D4"],
        "varga_note": "D2/D4 yalniz ortak kaynak ve ev bağlami icin",
        "timing": "Vimśottarī | iliski/evlilik penceresi | transit tetik | hazır oluş",
        "jaimini": "UL, DK, A7, D9 Kārakāṃśa paralel referans",
        "counter_focus": "7L/Venüs/D9 zayifligi, 2. ev dayaniklilik baskisi, bağlam uyumsuzlugu",
        "allowed": [
            "bağlanma kapasitesi", "ilişki dayanıklılık koşulları",
            "geniş resmîleşme penceresi", "müzakere isteyen alanlar",
        ],
        "blocked": [
            "garanti evlilik", "eş kimliği",
            "kesin düğün tarihi", "boşanma kaçınılmazlığı",
        ],
        "context_questions": [
            "Mevcut medeni durum?", "Karar aciliyeti?",
            "Aile ve kültür beklentisi?",
        ],
        "risk_level": "R2-SENSITIVE",
        "production_status": "CORE-WITH-HUMAN-REVIEW",
        "human_review": True,
    },
    "P02-BIZ": {
        "name": "İş Ortaklığı ve Sözleşme",
        "category": "Partnership role fit, governance risk, contract conditions",
        "excluded": ["personal romance", "employment career only", "investment return"],
        "surfaces": [
            "Lagna", "7. ev/lord", "10. ev/lord", "11. ev/lord", "2. ev/lord",
            "Merkür", "Satürn", "Mars", "Jüpiter", "Venüs", "risk/karşı kanıt",
        ],
        "varga_required": ["D10"],
        "varga_support": ["D2", "D4"],
        "varga_note": "D2 para, D4 varlik bağlaminda",
        "timing": "Vimśottarī erişim | sözleşme/başlangıç penceresi | nitelik",
        "jaimini": "A7, A10, AL, AmK paralel görünürlük karşılaştırması",
        "counter_focus": "8./12. ev yükümlülük, Merkür/Satürn yönetişim zayıflığı, sözleşme boşlukları",
        "allowed": [
            "rol uyumu", "yönetişim riski",
            "müzakere koşulları", "geniş karar penceresi",
        ],
        "blocked": [
            "hukuki sonuç garantisi", "ortak dürüstlüğü kesinliği",
            "yatırım getirisi garantisi",
        ],
        "context_questions": [
            "Ortaklık türü ve sektör?", "Sözleşme aşaması?",
            "Finansal ve hukuki danışman var mı?",
        ],
        "risk_level": "R2-SENSITIVE",
        "production_status": "CORE-WITH-LEGAL-FINANCIAL-DISCLAIMER",
        "human_review": True,
    },
    "P03-CAR": {
        "name": "Kariyer ve Kamusal Rol",
        "category": "Professional direction, role, work environment, status, leadership, public visibility",
        "excluded": ["income amount only", "business ownership contract", "education only"],
        "surfaces": [
            "Lagna/lord", "10. ev/lord", "6. ev", "2. ev", "11. ev",
            "Güneş", "Satürn", "Merkür", "Jüpiter", "Mars",
            "yoga/bhaṅga", "karşı kanıt",
        ],
        "varga_required": ["D10"],
        "varga_support": ["D24", "D2"],
        "varga_note": "D24 eğitim/yetiştirme, D2 kazanç alt konusunda",
        "timing": "Vimśottarī | kariyer erişimi | yavaş transit penceresi | eylem/hazır oluş",
        "jaimini": "AmK, AL, A10 paralel; Chara Daśā research-only",
        "counter_focus": "D10 teyit etmemesi, 6./10. ev çatışması, zamanlama durgunluğu",
        "allowed": [
            "rol eğilimleri", "çalışma ortamı uyumu",
            "liderlik/hizmet dengesi", "geniş fırsat penceresi",
        ],
        "blocked": [
            "tek kaçınılmaz meslek", "garanti terfi", "işveren zihni okuma",
        ],
        "context_questions": [
            "Mevcut rol ve sektör?", "Çalışan, kurucu veya serbest?",
            "İstenen değişim?", "Kısıt ve yeterlilikler?",
        ],
        "risk_level": "R1-CONTEXT",
        "production_status": "CORE-WITH-CONTEXT",
        "human_review": False,
    },
    "P04-WEA": {
        "name": "Gelir, Servet ve Varlik",
        "category": "Resource pattern, cash-flow, accumulation conditions",
        "excluded": ["career role only", "property relocation only", "legal debt process"],
        "surfaces": [
            "2. ev/lord", "11. ev/lord", "5. ev/lord", "9. ev/lord", "Lagna",
            "Jüpiter", "Merkür", "Venüs", "Satürn",
            "Dhana/Daridra ağları", "karşı kanıt",
        ],
        "varga_required": ["D2"],
        "varga_support": ["D10", "D4", "D11"],
        "varga_note": "D10 iş geliri, D4 mülk varlığı, D11 kazanç desteği",
        "timing": "Vimśottarī kaynak portföyü | nakit akışı penceresi | nitelik",
        "jaimini": "AL, A2, A11 arūḍha kaynak görünürlüğü",
        "counter_focus": "Daridra/harcama/borç ağı, D2 teyit etmemesi",
        "allowed": [
            "kaynak örüntüsü", "nakit akışı oynaklığı",
            "birikim koşulları", "geniş destekleyici/baskılı dönem",
        ],
        "blocked": [
            "yatırım tavsiyesi", "garanti servet",
            "kesin gelir miktarı", "borç kapanma kesinliği",
        ],
        "context_questions": [
            "Gelir kaynağı türü?", "Mevcut yükümlülükler?",
            "Finansal danışman var mı?",
        ],
        "risk_level": "R2-SENSITIVE",
        "production_status": "CORE-WITH-FINANCIAL-LIMIT",
        "human_review": True,
    },
    "P05-PRO": {
        "name": "Mülk, Yerleşim ve Yabancı Yaşam",
        "category": "Settlement pattern, mobility, property and relocation conditions",
        "excluded": ["income amount only", "family relationship only", "visa legal process"],
        "surfaces": [
            "4. ev/lord", "9. ev/lord", "12. ev/lord", "Lagna",
            "Ay", "Mars", "Venüs", "Satürn", "Rahu", "karşı kanıt",
        ],
        "varga_required": ["D4"],
        "varga_support": ["D9", "D12", "D2"],
        "varga_note": "D2 karşılanabilirlik; D16 araç için gerekli fakat motorda yok",
        "timing": "Vimśottarī | taşınma/mülk penceresi | transit tetik | kaynak hazırlığı",
        "jaimini": "A4, A12, AL; Chara Daśā yalnız karşılaştırma",
        "counter_focus": "4. ev istikrarı ile 9./12. ev hareketliliği çatışması, karşılanabilirlik ve hukuki kısıt",
        "allowed": [
            "yerleşim örüntüsü", "hareketlilik ve köklenme dengesi",
            "geniş taşınma/mülk penceresi", "pratik koşullar",
        ],
        "blocked": [
            "vize onayi", "mülk kârı garantisi",
            "bağlamsız kesin taşınma tarihi",
        ],
        "context_questions": [
            "Mevcut yerleşim ve statü?", "Hedef ülke veya şehir?",
            "Bütçe ve hukuki kısıtlar?",
        ],
        "risk_level": "R2-SENSITIVE",
        "production_status": "CORE-WITH-CONTEXT",
        "human_review": True,
    },
    "P06-CHI": {
        "name": "Çocuk, Ebeveynlik ve Aile",
        "category": "Parenting pattern, family role, family development",
        "excluded": ["fertility diagnosis", "custody legal process", "marriage decision"],
        "surfaces": [
            "5. ev/lord", "Jüpiter", "Lagna", "Ay",
            "2. ev", "4. ev", "9. ev", "koruyucu/karşı kanıt",
        ],
        "varga_required": ["D7"],
        "varga_support": ["D12", "D9", "D4"],
        "varga_note": "D12 ebeveyn/soy, D9 genel teyit",
        "timing": "Vimśottarī | cocuk/aile erişimi | transit penceresi | hazır oluş",
        "jaimini": "PK/MK/PiK profile bağlı; A5/A4 paralel",
        "counter_focus": "D1/D7 uyumsuzlugu, tibbi ve riza bağlami, koruyucu zayifligi",
        "allowed": [
            "ebeveynlik örüntüsü", "aile rolü",
            "geniş aile gelişim penceresi", "destek ihtiyaçları",
        ],
        "blocked": [
            "doğurganlık teşhisi", "garanti doğum",
            "çocuk kişiliği kesinliği", "velayet sonucu",
        ],
        "context_questions": [
            "Mevcut aile durumu?", "Tıbbi değerlendirme var mı?",
            "Ortak rıza mevcut mu?",
        ],
        "risk_level": "R3-ACUTE-WHEN-MEDICAL",
        "production_status": "HUMAN-REVIEW",
        "human_review": True,
    },
    "P07-EDU": {
        "name": "Eğitim, Beceri ve Sınav",
        "category": "Learning pattern, study conditions, readiness",
        "excluded": ["career outcome only", "IQ measurement", "institution guarantee"],
        "surfaces": [
            "4. ev/lord", "5. ev/lord", "9. ev/lord",
            "Merkür", "Jüpiter", "Ay", "Lagna", "karşı kanıt",
        ],
        "varga_required": ["D24"],
        "varga_support": ["D9", "D10"],
        "varga_note": "D10 mesleki kullanım bağlamında",
        "timing": "Vimśottarī | çalışma/sınav penceresi | hızlı tetik | hazır oluş",
        "jaimini": "PK/AmK/Kārakāṃśa isteğe bağlı paralel",
        "counter_focus": "D24 teyit etmemesi, hazırlık/kaynak boşluğu, zamanlama uyumsuzluğu",
        "allowed": [
            "öğrenme örüntüsü", "çalışma koşulları",
            "hazır oluş penceresi", "destek isteyen alanlar",
        ],
        "blocked": [
            "IQ puanı", "garanti sınav sonucu", "belirli kurum garantisi",
        ],
        "context_questions": [
            "Mevcut eğitim durumu?", "Hedef alan ve sınav?",
            "Zaman ve kaynak kısıtı?",
        ],
        "risk_level": "R1-CONTEXT",
        "production_status": "CORE-WITH-CONTEXT",
        "human_review": False,
    },
    "P08-HLT": {
        "name": "Sağlık, Canlılık ve Bakım",
        "category": "Stress and vitality pattern, rest and care conditions",
        "excluded": ["disease diagnosis", "treatment plan", "medication decision"],
        "surfaces": [
            "Lagna/lord", "Güneş", "Ay", "6. ev", "8. ev", "12. ev",
            "Mars", "Satürn", "Jüpiter", "koruyucu/karşı kanıt", "guvenlik",
        ],
        "varga_required": [],
        "varga_support": ["D6", "D30", "D12"],
        "varga_note": "D6 yalniz guclu dogum verisi kapisiyla; D30 zorluk bağlami; tek basina teshis yok",
        "timing": "Yalnız güvenlik kapısından sonra geniş stres/bakım penceresi",
        "jaimini": "Yüksek riskli literal Jaimini dili bloklu",
        "counter_focus": "Koruyucu faktörler ve klinik kanıt literal risk dilini geçersiz kılar",
        "allowed": [
            "stres/canlılık örüntüsü", "dinlenme ve destek koşulları",
            "geniş ve teşhis dışı bakım penceresi",
        ],
        "blocked": [
            "hastalık teşhisi", "ölüm veya ömür",
            "ilaç değişikliği", "acil durumda güven verme",
        ],
        "context_questions": [
            "Mevcut tıbbi takip var mı?", "Akut şikâyet var mı?",
            "Hekim değerlendirmesi yapıldı mı?",
        ],
        "risk_level": "R3-ACUTE",
        "production_status": "REFER/REWRITE-HUMAN-REVIEW",
        "human_review": True,
    },
    "P09-LIT": {
        "name": "Çatışma, Hukuk ve Kriz",
        "category": "Pressure pattern, negotiation and escalation conditions",
        "excluded": ["court outcome", "criminal determination", "medical crisis"],
        "surfaces": [
            "6. ev/lord", "7. ev/lord", "8. ev/lord", "10. ev/lord", "12. ev/lord",
            "Mars", "Satürn", "Merkür", "Jüpiter", "Rahu", "Ketu",
            "koruyucu/karşı kanıt",
        ],
        "varga_required": [],
        "varga_support": ["D30", "D10", "D4", "D9"],
        "varga_note": "D30 zorluk, D10 mesleki uyuşmazlık, D4 varlık uyuşmazlığı; veri kapısı zorunlu",
        "timing": "Vimśottarī baski erişimi | yavaş transit penceresi | hızlı tetik | kaynak",
        "jaimini": "A6/A7/A8 ve burç dönemi yalnız karşılaştırma",
        "counter_focus": "Jüpiter/koruma/uzlasma faktorleri, usul ve hukuki bağlam",
        "allowed": [
            "baskı örüntüsü", "müzakere/tırmanma koşulları",
            "geniş dikkat penceresi", "kaynak ihtiyaçları",
        ],
        "blocked": [
            "mahkeme sonucu", "cezai suçluluk",
            "karşı taraf davranışı kesinliği", "ölüm veya felaket",
        ],
        "context_questions": [
            "Sureç hangi asamada?", "Avukat var mı?",
            "Uzlaşma seçeneği açık mı?",
        ],
        "risk_level": "R3-ACUTE",
        "production_status": "HUMAN-REVIEW/LEGAL-LIMIT",
        "human_review": True,
    },
    "P10-SPI": {
        "name": "Ruhsal Yön, Pratik ve Anlam",
        "category": "Practice style, meaning-making, discipline conditions",
        "excluded": ["mokṣa certainty", "past-life claim as fact", "guru command"],
        "surfaces": [
            "5. ev/lord", "9. ev/lord", "12. ev/lord",
            "Jüpiter", "Ketu", "Satürn", "Ay", "Güneş", "Lagna",
            "karşı kanıt/bağlam",
        ],
        "varga_required": ["D20"],
        "varga_support": ["D9", "D60"],
        "varga_note": "D20 yalnız doğum saati kapısı açıkken; D60 yardımcı, ana hüküm değil",
        "timing": "Pratik/inziva hazır oluş pencereleri; aydınlanma tahmini yok",
        "jaimini": "AK/Kārakāṃśa paralel; metafizik iddialar EvidenceAtom dışında",
        "counter_focus": "Kacis egilimi, saglik/ruh sagligi bağlami, D20 veri hassasiyeti",
        "allowed": [
            "pratik biçimi", "anlam kurma örüntüsü",
            "disiplin/destek koşulları", "geniş pratik penceresi",
        ],
        "blocked": [
            "mokṣa kesinliği", "geçmiş yaşam anlatısını olgu sayma",
            "ruhsal üstünlük", "guru emri",
        ],
        "context_questions": [
            "Mevcut pratik var mı?", "Gelenek veya ekol bağı?",
            "Ruh sağlığı desteği var mı?",
        ],
        "risk_level": "R2-SENSITIVE",
        "production_status": "CORE-WITH-EPISTEMIC-LIMIT",
        "human_review": True,
    },
    "P11-TIM": {
        "name": "Zamanlama ve Öngörü İletişimi",
        "category": "Cross-cutting timing communication layer",
        "excluded": ["guaranteed date", "activation equals event"],
        "surfaces": ["konuya özgü vaat", "karşı kanıt", "bağlam"],
        "varga_required": [],
        "varga_support": [],
        "varga_note": "Konuya özgü",
        "timing": "natal potansiyel | daśā erişimi | yapısal pencere | tetik | nitelik | hazır oluş | eylem",
        "jaimini": "Compare-only profiller etiketli kalır",
        "counter_focus": "Natal vaat yok, daśā erişimi yok, hazır oluş eksik, profil ayrismasi",
        "allowed": [
            "aktivasyon mevcut", "pencere daralıyor",
            "hazır oluş uyumsuz", "olay kanıtı yok",
        ],
        "blocked": [
            "transit çalıştı/çalışmadı sadeleştirmesi",
            "garanti tarih", "aktivasyon = olay",
        ],
        "context_questions": ["Hangi konu?", "Karar aciliyeti?"],
        "risk_level": "TOPIC-DEPENDENT",
        "production_status": "CORE-CROSS-CUTTING",
        "human_review": False,
    },
    "GENERAL": {
        "name": "Genel Harita Analizi",
        "category": "Whole-chart operating system, no single topic judgment",
        "excluded": ["topic-specific final judgment without its own pack"],
        "surfaces": [
            "Lagna/lord", "Ay ve Janma Nakṣatra", "Güneş",
            "işlevsel lordluklar", "dispozitör ağı", "güç katmanı", "karşı kanıt",
        ],
        "varga_required": ["D9"],
        "varga_support": ["D10", "D24", "D4"],
        "varga_note": "Genel analizde varga yalnız D1 vaadini teyit eder",
        "timing": "Vimśottarī genel erişim | geniş transit teması",
        "jaimini": "AK/AmK/Kārakāṃśa paralel etiketli",
        "counter_focus": "Güç ile konumsal zorluğun birlikte değerlendirilmesi",
        "allowed": [
            "yaşam örüntüsü", "güçlü ve zorlayıcı mekanizmalar",
            "gelişim alanı", "geniş dönem teması",
        ],
        "blocked": [
            "kesin kader", "değişmez kişilik",
            "konu paketi olmadan kesin konu hükmü",
        ],
        "context_questions": ["Analiz amacı?", "Odaklanılacak alan var mı?"],
        "risk_level": "R1-CONTEXT",
        "production_status": "CORE-WITH-CONTEXT",
        "human_review": False,
    },
}


# --------------------------------------------------------------------------
# Yardimcilar
# --------------------------------------------------------------------------

def _esc(value):
    """Markdown tablo hucresinde | karakterini kacir."""
    return str(value).replace("|", "\\|")


def _fmt_list(items, empty="yok"):
    if not items:
        return empty
    return ", ".join(str(x) for x in items)


def _bullet_list(items, empty="- yok"):
    if not items:
        return [empty]
    return ["- " + str(x) for x in items]


# --------------------------------------------------------------------------
# Veri kapisi — motorun data_quality ciktisindan okunur, uydurulmaz
# --------------------------------------------------------------------------

# Kunye: RUL-PH3-0008, RUL-T05-0001 (ACTIVE)

CONFIDENCE_ORDER = {"very_low": 0, "low": 1, "medium": 2, "high": 3}


def _min_confidence(*values):
    known = [v for v in values if v in CONFIDENCE_ORDER]
    if not known:
        return "low"
    return min(known, key=lambda v: CONFIDENCE_ORDER[v])


def resolve_data_gate(chart, pack_id=None):
    """Veri kapisini chart['data_quality'] uzerinden cozer. Hesap yapmaz."""
    chart = chart or {}
    birth = chart.get("birth") or {}
    dq = chart.get("data_quality") or {}

    supported = list(dq.get("supported_vargas") or [])
    varga_conf = dict(dq.get("varga_interpretation_confidence") or {})
    verified = list(dq.get("person_verified_vargas") or [])

    conf_label = (dq.get("birth_time_confidence_label")
                  or birth.get("time_confidence_label") or "")
    conf_raw = (dq.get("birth_time_confidence")
                or birth.get("time_confidence") or "")

    reference_frame = dq.get("reference_frame") or "birth_lagna"
    lagna_conf = (
        dq.get("reference_lagna_interpretation_confidence")
        if reference_frame == "chandra_lagna"
        else dq.get("lagna_interpretation_confidence")
    ) or ""
    house_conf = dq.get("house_interpretation_confidence") or ""
    sign_conf = dq.get("planet_sign_interpretation_confidence") or ""
    engine_floor = _min_confidence(lagna_conf, house_conf, sign_conf)
    cap = engine_floor
    cap_reasons = []
    if engine_floor != "high":
        cap_reasons.append("motor yorum güveni: %s" % engine_floor)
    if reference_frame == "chandra_lagna":
        cap_reasons.append("ev çerçevesi Chandra Lagna")

    # Medium varga yorumlanabilir; low/very_low varga hüküm üretmez.
    blocked = []
    for div, conf in sorted(varga_conf.items()):
        if conf in {"low", "very_low"}:
            blocked.append("%s (güven: %s)" % (div, conf))

    conflict = []
    pack = TOPIC_PACK_REGISTRY.get(pack_id) if pack_id else None
    if pack:
        for div in pack.get("varga_required", []):
            confidence = varga_conf.get(div)
            if div == "D1" and reference_frame == "chandra_lagna":
                continue
            if not confidence:
                conflict.append("%s (güven kaydı yok)" % div)
            elif confidence in {"low", "very_low"}:
                conflict.append("%s (güven: %s)" % (div, confidence))
            else:
                cap = _min_confidence(cap, confidence)

    passed = engine_floor in {"medium", "high"} and not conflict

    return {
        "confidence_raw": conf_raw or "belirtilmemis",
        "confidence_label": conf_label or "belirtilmemis",
        "birth_time_declaration": dq.get("birth_time_declaration") or conf_raw or "belirtilmemis",
        "customer_declaration_basis": bool(dq.get("customer_declaration_basis")),
        "accepted_as_rectified": bool(dq.get("accepted_as_rectified")),
        "reference_frame": reference_frame,
        "calculation_reference_time": dq.get("calculation_reference_time"),
        "independent_verification": bool(verified),
        "verified_vargas": verified,
        "lagna_confidence": lagna_conf or "-",
        "house_confidence": house_conf or "-",
        "sign_confidence": sign_conf or "-",
        "interpretation_policy": dq.get("interpretation_policy") or "-",
        "supported_vargas": supported,
        "blocked_techniques": blocked,
        "required_conflict": conflict,
        "confidence_cap": cap,
        "cap_reasons": cap_reasons,
        "engine_notes": list(dq.get("notes") or []),
        "passed": passed,
        "has_data_quality": bool(dq),
    }



# --------------------------------------------------------------------------

def package_contract_markdown(pack_id):
    """Blok 2 - Paket sozlesmesi."""
    pack = TOPIC_PACK_REGISTRY.get(pack_id)
    if not pack:
        return ""

    lines = [
        "## Paket Sözleşmesi",
        "",
        "| Alan | Değer |",
        "| --- | --- |",
        f"| Paket kimliği | {pack_id} |",
        f"| Kategori | {_esc(pack['name'])} |",
        f"| Kapsam | {_esc(pack['category'])} |",
        f"| Hariç | {_esc(_fmt_list(pack['excluded']))} |",
        f"| Risk seviyesi | {_esc(pack['risk_level'])} |",
        f"| Üretim statüsü | {_esc(pack['production_status'])} |",
        f"| İnsan denetimi | {'zorunlu' if pack['human_review'] else 'gerekmiyor'} |",
        f"| Zorunlu varga | {_esc(_fmt_list(pack['varga_required']))} |",
        f"| Destek varga | {_esc(_fmt_list(pack['varga_support']))} |",
        f"| Varga notu | {_esc(pack['varga_note'])} |",
        f"| Zamanlama zinciri | {_esc(pack['timing'])} |",
        f"| Jaimini kullanımı | {_esc(pack['jaimini'])} |",
        f"| Künye | RUL-PH5-*-01/02/03 (ACTIVE) |",
        "",
        "**Zorunlu teknik yüzeyler**",
        "",
    ]
    lines += _bullet_list(pack["surfaces"])
    lines += [
        "",
        "**Aranacak karşı kanıt**",
        "",
        f"- {pack['counter_focus']}",
        "",
        "**İzinli hüküm dili**",
        "",
    ]
    lines += _bullet_list(pack["allowed"])
    lines += [
        "",
        "**Bloklanan hüküm dili** (teknik destek görünse bile üretilemez)",
        "",
    ]
    lines += _bullet_list(pack["blocked"])
    lines += [
        "",
        "**Sorulacak bağlam soruları**",
        "",
    ]
    lines += _bullet_list(pack["context_questions"])
    lines.append("")
    return "\n".join(lines)


def package_data_gate_markdown(chart, pack_id=None):
    """Blok 3 — Veri kapisi."""
    g = resolve_data_gate(chart, pack_id)

    if not g["has_data_quality"]:
        return "\n".join([
            "## Veri Kapısı",
            "",
            "- Motor `data_quality` bloğu üretmedi. Kapı değerlendirilemedi.",
            "- Bu paket üzerinden kesin hüküm kurulmaz; sonuç INCOMPLETE sayılır.",
            "",
        ])

    lines = [
        "## Veri Kapısı",
        "",
        "| Alan | Değer |",
        "| --- | --- |",
        "| Doğum saati güveni | %s (%s) |" % (
            _esc(g["confidence_label"]), _esc(g["confidence_raw"])),
        "| Müşteri beyanı | %s |" % _esc(g["birth_time_declaration"]),
        "| Müşteri beyanı esas mı | %s |" % (
            "evet" if g["customer_declaration_basis"] else "hayır"),
        "| Rektifikasyonlu kabul | %s |" % (
            "evet" if g["accepted_as_rectified"] else "hayır"),
        "| Ev referansı | %s |" % _esc(g["reference_frame"]),
        "| Teknik hesaplama saati | %s |" % _esc(
            g["calculation_reference_time"] or "doğum saati"),
        "| Formül karşılaştırma kaydı | %s |" % (
            "var (%s)" % _esc(_fmt_list(g["verified_vargas"]))
            if g["independent_verification"] else "yok"),
        "| Lagna yorum güveni | %s |" % _esc(g["lagna_confidence"]),
        "| Ev yorum güveni | %s |" % _esc(g["house_confidence"]),
        "| Burç yorum güveni | %s |" % _esc(g["sign_confidence"]),
        "| Saat politikası | %s |" % _esc(g["interpretation_policy"]),
        "| Kapı durumu | %s |" % ("geçti" if g["passed"] else "KAPALI"),
        "| Veri güven tavanı | data=%s |" % g["confidence_cap"],
        "| Künye | RUL-PH3-0008, RUL-T05-0001 (ACTIVE) |",
        "",
        "**Güven tavanının gerekçesi**",
        "",
    ]
    lines += _bullet_list(g["cap_reasons"], "- tavanı düşüren bir koşul yok")

    lines += [
        "",
        "**Kapalı veya sınırlı teknikler**",
        "",
    ]
    lines += _bullet_list(g["blocked_techniques"], "- yok")

    if g["required_conflict"]:
        lines += [
            "",
            "**UYARI — bu paketin zorunlu vargası kapalı**",
            "",
        ]
        lines += _bullet_list(g["required_conflict"])
        lines += [
            "- Sonuç INCOMPLETE işaretlenmelidir; bu varga üzerinden hüküm kurulamaz.",
        ]

    if g["engine_notes"]:
        lines += [
            "",
            "**Motor notları**",
            "",
        ]
        lines += _bullet_list(g["engine_notes"])

    lines += [
        "",
        "- Kapalı teknik listesindeki varga tablosu pakette bulunsa bile ana hüküm kanıtı olarak kullanılamaz.",
        "- `data` ekseni bu tavanın üzerine çıkamaz; `overall` güven `data`'dan yüksek olamaz.",
        "",
    ]
    return "\n".join(lines)



# --------------------------------------------------------------------------
# Blok 4 — Zorunlu yüzey denetimi
# Künye: RUL-PH5-*-02, RUL-T11-0004, RUL-INT-0005 (ACTIVE)
# --------------------------------------------------------------------------

PLANET_TR_EN = {
    "güneş": "Sun", "gunes": "Sun",
    "ay": "Moon",
    "mars": "Mars",
    "merkür": "Mercury", "merkur": "Mercury",
    "jüpiter": "Jupiter", "jupiter": "Jupiter",
    "venüs": "Venus", "venus": "Venus",
    "satürn": "Saturn", "saturn": "Saturn",
    "rahu": "Rahu",
    "ketu": "Ketu",
}

DUSTHANA = (6, 8, 12)


def _planets_by_name(chart):
    out = {}
    for p in (chart.get("planets") or []):
        if isinstance(p, dict) and p.get("name"):
            out[p["name"]] = p
    return out


def _houses_by_number(chart):
    out = {}
    for h in (chart.get("houses") or []):
        if isinstance(h, dict) and h.get("house") is not None:
            out[h["house"]] = h
    return out


def _classify_surface(label):
    """Yüzey etiketini denetlenebilir bir türe çevirir."""
    low = str(label).strip().lower()
    import re as _re
    m = _re.match(r"^(\d+)\.\s*(ev|bhāva|bhava)", low)
    if m:
        return ("house", int(m.group(1)))
    if low.startswith("lagna"):
        return ("lagna", None)
    for tr, en in PLANET_TR_EN.items():
        if low == tr or low.startswith(tr + " ") or low.startswith(tr + "/"):
            return ("planet", en)
    if "karşı kanıt" in low or "karsi kanit" in low or "counter" in low:
        return ("counter", None)
    if "yoga" in low:
        return ("yoga", None)
    return ("other", None)


def audit_surfaces(chart, pack_id):
    """Zorunlu yüzeylerin chart içinde karşılığı var mı denetler."""
    pack = TOPIC_PACK_REGISTRY.get(pack_id)
    if not pack:
        return None

    chart = chart or {}
    planets = _planets_by_name(chart)
    houses = _houses_by_number(chart)
    lordships = chart.get("lordships") or {}
    vargas = chart.get("vargas") or {}
    yogas = chart.get("yogas") or {}

    covered, missing, unaudited = [], [], []

    for label in pack.get("surfaces", []):
        kind, key = _classify_surface(label)
        if kind == "house":
            has_house = key in houses
            has_lord = bool(
                (houses.get(key) or {}).get("lord")
                or (lordships.get(str(key)) or lordships.get(key))
            )
            (covered if (has_house and has_lord) else missing).append(label)
        elif kind == "planet":
            (covered if key in planets else missing).append(label)
        elif kind == "lagna":
            (covered if chart.get("lagna") else missing).append(label)
        elif kind == "yoga":
            has = bool(yogas.get("matches") or yogas.get("yogas") or yogas)
            (covered if has else missing).append(label)
        elif kind == "counter":
            covered.append(label)  # blok 6 tarafından üretilir
        else:
            unaudited.append(label)

    varga_missing = []
    for div in pack.get("varga_required", []):
        if not (vargas.get(div) or {}):
            varga_missing.append(div)

    complete = not missing and not varga_missing
    return {
        "required_count": len(pack.get("surfaces", [])),
        "covered": covered,
        "missing": missing,
        "unaudited": unaudited,
        "varga_required": list(pack.get("varga_required", [])),
        "varga_missing": varga_missing,
        "status": "COMPLETE" if complete else "INCOMPLETE",
    }


def package_surface_audit_markdown(chart, pack_id):
    """Blok 4 — Zorunlu yüzey denetimi."""
    a = audit_surfaces(chart, pack_id)
    if not a:
        return ""

    lines = [
        "## Zorunlu Yüzey Denetimi",
        "",
        "| Alan | Değer |",
        "| --- | --- |",
        "| Zorunlu yüzey sayısı | %d |" % a["required_count"],
        "| Kapsanan | %d |" % len(a["covered"]),
        "| Eksik | %d |" % len(a["missing"]),
        "| Denetlenemeyen | %d |" % len(a["unaudited"]),
        "| Zorunlu varga | %s |" % _esc(_fmt_list(a["varga_required"])),
        "| Eksik varga | %s |" % _esc(_fmt_list(a["varga_missing"])),
        "| Denetim sonucu | **%s** |" % a["status"],
        "| Künye | RUL-PH5-*-02, RUL-T11-0004 (ACTIVE) |",
        "",
    ]

    if a["missing"] or a["varga_missing"]:
        lines += ["**Eksik yüzeyler**", ""]
        lines += _bullet_list(a["missing"] + ["varga: " + d for d in a["varga_missing"]])
        lines += [
            "",
            "- Eksik yüzey varken bu konuda kesin hüküm kurulamaz.",
            "- Aşama 1 çıktısı `mandatory_surfaces_covered.missing` alanında bunları taşımalıdır.",
            "",
        ]
    else:
        lines += ["- Zorunlu yüzeylerin tamamı pakette mevcut.", ""]

    if a["unaudited"]:
        lines += [
            "**Otomatik denetlenemeyen yüzeyler** (elle kontrol edilir)",
            "",
        ]
        lines += _bullet_list(a["unaudited"])
        lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------
# Blok 6 — Natal karşı kanıt
# Künye: RUL-INT-0013, RUL-PH5-*-02, SYS-005 (karşı kanıt zorunlu)
# --------------------------------------------------------------------------

def collect_natal_counter_evidence(chart, pack_id):
    """Konu yüzeylerindeki gezegenler için otomatik karşı kanıt taraması."""
    pack = TOPIC_PACK_REGISTRY.get(pack_id)
    if not pack:
        return None

    chart = chart or {}
    planets = _planets_by_name(chart)
    houses = _houses_by_number(chart)

    # Konu ile ilgili gezegen kümesi: yüzeylerde adı geçenler + ev lordları
    targets = []
    for label in pack.get("surfaces", []):
        kind, key = _classify_surface(label)
        if kind == "planet" and key not in targets:
            targets.append(key)
        elif kind == "house":
            lord = (houses.get(key) or {}).get("lord")
            if lord and lord not in targets:
                targets.append(lord)
        elif kind == "lagna":
            lord = (houses.get(1) or {}).get("lord")
            if lord and lord not in targets:
                targets.append(lord)

    counter, conditions = [], []
    for name in targets:
        p = planets.get(name)
        if not p:
            continue
        dignity = p.get("dignity") or {}
        combust = p.get("combustion") or {}
        motion = p.get("motion") or {}
        house = p.get("house")
        sign = p.get("sign_tr") or p.get("sign") or ""

        if dignity.get("neecha"):
            counter.append("%s düşkün (neecha) — %s" % (name, sign))
        elif dignity.get("essential") == "debilitated":
            counter.append("%s düşkün — %s" % (name, sign))
        elif dignity.get("essential") == "enemy":
            counter.append("%s düşman burçta — %s" % (name, sign))

        if combust.get("is_combust"):
            counter.append("%s yanmış (Güneş'ten %.1f°, eşik %.1f°)" % (
                name,
                combust.get("distance_from_sun") or 0.0,
                combust.get("threshold") or 0.0,
            ))

        if house in DUSTHANA:
            counter.append("%s dusthana yerleşimi — %d. ev" % (name, house))

        if motion.get("retrograde"):
            conditions.append("%s retro — teslim biçimi koşullu, tek başına karşı kanıt değil" % name)
        if motion.get("speed_status") in ("slow", "stationary"):
            conditions.append("%s hız durumu: %s" % (name, motion.get("speed_status")))

    # Ev lordunun dusthanada olması, o evin konusu için ayrı karşı kanıt
    for label in pack.get("surfaces", []):
        kind, key = _classify_surface(label)
        if kind != "house":
            continue
        lord = (houses.get(key) or {}).get("lord")
        lp = planets.get(lord) if lord else None
        if lp and lp.get("house") in DUSTHANA:
            item = "%d. ev lordu %s dusthanada (%d. ev) — bu alanın teslimi dolaylı" % (
                key, lord, lp.get("house"))
            if item not in counter:
                counter.append(item)

    # Graha Yuddha (varsa)
    war = chart.get("graha_yuddha") or {}
    if isinstance(war, dict):
        for k in ("pairs", "results", "matches"):
            for item in (war.get(k) or []):
                if isinstance(item, dict):
                    counter.append("Graha Yuddha: %s" % _fmt_list(
                        [str(v) for v in item.values()][:3]))

    return {
        "targets": targets,
        "counter": counter,
        "conditions": conditions,
        "focus": pack.get("counter_focus", ""),
    }


def package_counter_evidence_markdown(chart, pack_id):
    """Blok 6 — Natal karşı kanıt."""
    c = collect_natal_counter_evidence(chart, pack_id)
    if not c:
        return ""

    lines = [
        "## Natal Karşı Kanıt",
        "",
        "- Bu liste API tarafından üretilmiştir; yorum içermez.",
        "- Karşı kanıt bulunmayan hüküm kurulamaz; bulunamadıysa gerekçesi yazılır.",
        "- Künye: RUL-INT-0013, SYS-005",
        "",
        "**Paketin aradığı karşı kanıt ekseni**",
        "",
        "- %s" % (c["focus"] or "belirtilmemiş"),
        "",
        "**Taranan göstergeler**",
        "",
        "- %s" % _fmt_list(c["targets"], "yok"),
        "",
        "**Bulunan karşı kanıtlar**",
        "",
    ]
    if c["counter"]:
        lines += _bullet_list(c["counter"])
    else:
        lines += [
            "- Otomatik taramada belirgin karşı kanıt saptanmadı.",
            "- Bu, karşı kanıt yok demek değildir; yorum aşamasında gerekçelendirilmelidir.",
        ]

    lines += [
        "",
        "**Koşullar** (karşı kanıt değil, teslim biçimini etkiler)",
        "",
    ]
    lines += _bullet_list(c["conditions"], "- kayıt yok")
    lines += [
        "",
        "- Bu tarama dignity, yanma, dusthana yerleşimi ve hareket durumuyla sınırlıdır.",
        "- SAV/BAV, varga teyidi ve daśā erişimi ayrı bölümlerde değerlendirilir.",
        "",
    ]
    return "\n".join(lines)
