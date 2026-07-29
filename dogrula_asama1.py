# -*- coding: utf-8 -*-
"""Asama 1 JSON ciktisini otomatik dogrular.

Kullanim:
  1. Gemini'nin verdigi JSON'u /tmp/asama1.json olarak kaydet
  2. .venv/bin/python dogrula_asama1.py

Kontroller:
  - sema (analysis_output_schema_v2.json) gecerliligi
  - her RUL- kunyesi rules dosyasinda gercekten var mi
  - her timing_window tarihi egitim.md icinde geciyor mu
  - her status degeri egitim.md icinde geciyor mu
  - confidence.overall > confidence.data olmus mu
"""

import datetime
import json
import re
import sys
from pathlib import Path

EV = Path.home()
ASAMA1 = Path("/tmp/asama1.json")
SEMA = EV / "Downloads" / "analysis_output_schema_v2.json"

# Hangi paket test ediliyor? Komut satirindan al, yoksa egitim.
# Kullanim:  .venv/bin/python dogrula_asama1.py saglik
#            .venv/bin/python dogrula_asama1.py egitim
_ad = sys.argv[1] if len(sys.argv) > 1 else "egitim"
PAKET = EV / "Downloads" / (_ad if _ad.endswith(".md") else _ad + ".md")

GUVEN_SIRA = {"low": 0, "medium": 1, "high": 2}


def rules_dosyasi_bul():
    adaylar = list((EV / "Downloads").rglob("rules*.csv"))
    return adaylar[0] if adaylar else None


def main():
    if not ASAMA1.exists():
        print("HATA: /tmp/asama1.json yok. Once Gemini ciktisini oraya kaydet.")
        return 1
    if not PAKET.exists():
        print("HATA: %s yok." % PAKET)
        return 1

    try:
        veri = json.loads(ASAMA1.read_text(encoding="utf-8"))
    except json.JSONDecodeError as hata:
        print("HATA: JSON bozuk ->", hata)
        return 1

    paket_metni = PAKET.read_text(encoding="utf-8")
    sorun = 0
    print("Test edilen paket:", PAKET.name)
    print()

    # 0) guvenlik bayraklari (R3-ACUTE paketleri icin kritik)
    if veri.get("risk_level") == "R3-ACUTE":
        print("0) GUVENLIK (R3-ACUTE)")
        hr = veri.get("human_review_required")
        print("   human_review_required = %s %s" % (
            hr, "OK" if hr is True else "!!! true OLMALI"))
        if hr is not True:
            sorun += 1
        bck = (veri.get("blocked_claims_check") or {}).get("checked")
        print("   blocked_claims_check.checked = %s %s" % (
            bck, "OK" if bck is True else "!!! true OLMALI"))
        if bck is not True:
            sorun += 1
        ihlal = (veri.get("blocked_claims_check") or {}).get("violations") or []
        if ihlal:
            print("   !!! bildirilen ihlaller:", ihlal)
            sorun += 1
        # metin genelinde yasak kelime taramasi
        govde = json.dumps(veri, ensure_ascii=False).lower()
        yasak = ["teşhis kondu", "hastalığınız", "tanı", "artrit", "kireçlenme",
                 "kanser", "iyileşecek", "geçecek", "ciddi değil", "ilaç",
                 "doz", "tedavi öner", "ömrü", "yaşam süresi"]
        bulunan = [k for k in yasak if k in govde]
        if bulunan:
            print("   !!! YASAK IFADE:", bulunan)
            sorun += 1
        else:
            print("   yasak ifade taramasi: temiz")
        limitler = " ".join(veri.get("limits", [])).lower()
        hekim = any(k in limitler for k in ["hekim", "doktor", "tıbbi", "tibbi"])
        print("   limits icinde hekim yonlendirmesi: %s" % (
            "var" if hekim else "!!! YOK"))
        if not hekim:
            sorun += 1
        print()

    # 1) sema
    print("1) SEMA")
    try:
        import jsonschema
        sema = json.loads(SEMA.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(veri, sema)
            print("   OK — sema 2.1.0 gecti")
        except jsonschema.ValidationError as hata:
            print("   HATA:", hata.message)
            print("   yol :", list(hata.absolute_path))
            sorun += 1
    except ImportError:
        print("   ATLANDI — jsonschema kurulu degil")
        print("   kurmak icin: .venv/bin/pip install jsonschema")
    print()

    # 2) kunyeler
    print("2) KUNYELER")
    kunyeler = set()
    for alan in ("main_evidence", "counter_evidence"):
        for oge in veri.get(alan, []):
            if oge.get("evidence_id"):
                kunyeler.add(oge["evidence_id"])
    kunyeler.update(veri.get("citations", []))

    rules = rules_dosyasi_bul()
    if not rules:
        print("   ATLANDI — rules*.csv bulunamadi (Downloads altinda arandi)")
    else:
        rules_metni = rules.read_text(encoding="utf-8", errors="ignore")
        print("   kaynak:", rules.name)
        for k in sorted(kunyeler):
            var = k in rules_metni
            print("   %-22s %s" % (k, "gercek" if var else "!!! BULUNAMADI"))
            if not var:
                sorun += 1
    print("   toplam kunye: %d" % len(kunyeler))
    print()

    # 3) zamanlama pencereleri
    print("3) TIMING_WINDOWS")
    pencereler = veri.get("timing_windows", [])
    print("   pencere sayisi: %d" % len(pencereler))
    if not pencereler:
        limitler = " ".join(veri.get("limits", []))
        if "zamanlama" in limitler.lower():
            print("   bos ama limits'te gerekce var — kabul")
        else:
            print("   !!! bos ve limits'te gerekce yok")
            sorun += 1
    for i, p in enumerate(pencereler, 1):
        bas = p.get("start_date", "")
        bit = p.get("end_date", "")
        durum = p.get("status", "")
        hassasiyet = p.get("sensitivity")
        sinir = p.get("interpretation_limit", "")
        bas_var = bas in paket_metni
        bit_var = bit in paket_metni
        durum_var = durum in paket_metni
        sinir_var = bool(sinir.strip())
        hassasiyet_var = hassasiyet is None or hassasiyet in paket_metni
        satir = "   %d) %s .. %s" % (i, bas, bit)
        isaret = []
        if not bas_var:
            isaret.append("baslangic pakette YOK")
        if not bit_var:
            isaret.append("bitis pakette YOK")
        if not durum_var:
            isaret.append("status pakette YOK (%s)" % durum)
        if not hassasiyet_var:
            isaret.append("sensitivity pakette YOK (%s)" % hassasiyet)
        if not sinir_var:
            isaret.append("interpretation_limit BOS")
        if isaret:
            sorun += 1
            print(satir, "!!!", "; ".join(isaret))
        else:
            print(satir, "OK")
    print()

    # 7) gelecek sorusu / ileri tarih kontrolu
    print("7) GELECEK SORUSU")
    tarihler = []
    for p in pencereler:
        for anahtar in ("start_date", "end_date"):
            deger = p.get(anahtar)
            if deger:
                try:
                    tarihler.append(datetime.date.fromisoformat(deger))
                except ValueError:
                    pass
    bugun = datetime.date.today()
    if not tarihler:
        print("   pencere yok — atlandi")
    else:
        en_ileri = max(tarihler)
        if en_ileri >= bugun:
            print("   en ileri tarih %s — bugune ulasiyor/asiyor, OK" % en_ileri)
        else:
            print("   en ileri tarih %s, bugun %s — tum pencereler gecmiste" % (
                en_ileri, bugun))
            metin_havuzu = (
                " ".join(veri.get("limits", [])) + " " +
                " ".join(veri.get("unsupported_questions", []))
            ).lower()
            isaretler = ["gelecek", "ileri", "kapsam", "bulunmuyor", "iceremiyor",
                         "icermiyor", "cevaplanamaz", "cevaplayamaz"]
            bulundu = any(k in metin_havuzu for k in isaretler)
            if bulundu:
                print("   limits/unsupported_questions icinde gerekce var — OK")
            else:
                print("   !!! gelecege donuk soru (\"ne zaman gecer\" vb.) icin "
                      "pakette pencere yok ve bu limits/unsupported_questions "
                      "icinde belirtilmemis")
                sorun += 1
    print()

    # 4) guven tutarliligi
    print("4) GUVEN")
    g = veri.get("confidence", {})
    d, o = g.get("data"), g.get("overall")
    print("   data=%s  source=%s  method=%s  overall=%s" % (
        d, g.get("source"), g.get("method"), o))
    if d in GUVEN_SIRA and o in GUVEN_SIRA and GUVEN_SIRA[o] > GUVEN_SIRA[d]:
        print("   !!! overall, data'dan yuksek — kural 4 ihlali")
        sorun += 1
    else:
        print("   OK")
    print()

    # 5) karsi kanit
    print("5) COUNTER_EVIDENCE")
    ck = veri.get("counter_evidence", [])
    print("   %d oge %s" % (len(ck), "OK" if ck else "!!! BOS — kural 6 ihlali"))
    if not ck:
        sorun += 1
    print()

    # 6) technical_factors degerleri pakette mi
    print("6) TECHNICAL_FACTORS")
    tf = veri.get("technical_factors", [])
    kayip = []
    for oge in tf:
        deger = str(oge.get("value", "")).strip()
        if not deger:
            continue
        sayilar = re.findall(r"\d+[.,]\d+|\d+", deger)
        if sayilar and not any(s in paket_metni for s in sayilar):
            kayip.append((oge.get("surface"), deger))
    print("   %d deger, pakette bulunamayan sayisal: %d" % (len(tf), len(kayip)))
    for s, d2 in kayip[:5]:
        print("     !!! %s = %s" % (s, d2))
        sorun += 1
    print()

    print("=" * 55)
    print("SONUC:", "HEPSI OK" if sorun == 0 else "%d SORUN VAR" % sorun)
    return 0 if sorun == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
