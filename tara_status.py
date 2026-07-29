# -*- coding: utf-8 -*-
"""Tum konu paketlerinin urettigi 'Durum' (status) ve 'Yorum Siniri'
degerlerini toplar. Sema enum'unu duzeltmek icin gercek envanter cikarir.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import app

CHART_YOLU = "/tmp/tam.json"
SEMA = Path.home() / "Downloads" / "analysis_output_schema_v2.json"

PAKETLER = [
    ("career", "_build_career_analysis_data_package_markdown"),
    ("health", "_build_health_analysis_data_package_markdown"),
    ("education", "_build_education_analysis_data_package_markdown"),
    ("family", "_build_family_analysis_data_package_markdown"),
    ("finance", "_build_finance_analysis_data_package_markdown"),
    ("relationship", "_build_relationship_analysis_data_package_markdown"),
    ("relocation", "_build_relocation_analysis_data_package_markdown"),
    ("legal", "_build_legal_analysis_data_package_markdown"),
    ("spiritual", "_build_spiritual_analysis_data_package_markdown"),
    ("character", "_build_character_analysis_data_package_markdown"),
    ("varshaphala", "_build_varshaphala_analysis_data_package_markdown"),
]

# tablo hucresinde status/limit gibi gorunen degerler: snake_case, uzun
DESEN = re.compile(r"^[a-z][a-z0-9_]{12,}$")


def main():
    if not Path(CHART_YOLU).exists():
        print("HATA: %s yok." % CHART_YOLU)
        return 1
    chart = json.load(open(CHART_YOLU))

    statusler = defaultdict(set)
    limitler = defaultdict(set)
    ek_sutunlar = defaultdict(set)

    for isim, fn_adi in PAKETLER:
        fn = getattr(app, fn_adi, None)
        if fn is None:
            print("!! %s bulunamadi, atlandi" % fn_adi)
            continue
        try:
            md = fn(chart, "levo", "Grup-01", transit_pack=None)
        except TypeError:
            md = fn(chart, "levo", "Grup-01")
        except Exception as hata:
            print("!! %-13s HATA: %s" % (isim, hata))
            continue

        basliklar = None
        for satir in md.split("\n"):
            if not satir.startswith("| "):
                continue
            hucreler = [h.strip() for h in satir.strip().strip("|").split("|")]
            if "Durum" in hucreler and "Yorum Sınırı" in hucreler:
                basliklar = hucreler
                # zamanlama tablosunda hangi ek sutunlar var
                bilinen = {"Sıra", "Başlangıç", "Bitiş", "Dasha Yolu",
                           "Aktivasyon", "Katmanlar", "İlk Kanıtlar",
                           "Durum", "Yorum Sınırı"}
                for h in hucreler:
                    if h not in bilinen:
                        ek_sutunlar[isim].add(h)
                continue
            if not basliklar or len(hucreler) != len(basliklar):
                continue
            for baslik, deger in zip(basliklar, hucreler):
                if baslik == "Durum" and DESEN.match(deger):
                    statusler[deger].add(isim)
                elif baslik == "Yorum Sınırı" and DESEN.match(deger):
                    limitler[deger].add(isim)

    sema = json.loads(SEMA.read_text(encoding="utf-8"))
    enum = set(sema["$defs"]["timing_window"]["properties"]["status"]["enum"])

    print("=" * 70)
    print("PAKETLERIN URETTIGI STATUS DEGERLERI")
    print("=" * 70)
    eksik = []
    for deger in sorted(statusler):
        var = deger in enum
        if not var:
            eksik.append(deger)
        print("%-58s %s" % (deger, "semada VAR" if var else "!!! SEMADA YOK"))
        print("   paketler: %s" % ", ".join(sorted(statusler[deger])))
    print()

    print("=" * 70)
    print("SEMADA OLUP HIC URETILMEYEN")
    print("=" * 70)
    for deger in sorted(enum - set(statusler)):
        print("  ", deger)
    print()

    print("=" * 70)
    print("ZAMANLAMA TABLOSUNDAKI EK SUTUNLAR (semada karsiligi olmayabilir)")
    print("=" * 70)
    for isim in sorted(ek_sutunlar):
        print("%-13s %s" % (isim, sorted(ek_sutunlar[isim])))
    print()

    print("=" * 70)
    print("FARKLI YORUM SINIRI DEGERI: %d adet" % len(limitler))
    print("=" * 70)
    for deger in sorted(limitler):
        print("  %s" % deger)
        print("     %s" % ", ".join(sorted(limitler[deger])))
    print()

    print("=" * 70)
    print("SONUC: semaya eklenmesi gereken %d status degeri" % len(eksik))
    for d in eksik:
        print("  ", d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
