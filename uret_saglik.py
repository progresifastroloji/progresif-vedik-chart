# -*- coding: utf-8 -*-
"""R3-ACUTE saglik paketi uretimi + on kontrol.

Ciktiyi ~/Downloads/saglik.md dosyasina yazar ve Gemini testine
gonderilmeden once yapisal kontrol listesini raporlar.
"""

import json
import unicodedata
from pathlib import Path

import app

CHART_YOLU = "/tmp/tam.json"
CIKTI = Path.home() / "Downloads" / "saglik.md"


def sadelestir(metin):
    return unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()


def main():
    if not Path(CHART_YOLU).exists():
        print("HATA: %s yok." % CHART_YOLU)
        return 1

    chart = json.load(open(CHART_YOLU))
    md = app._build_health_analysis_data_package_markdown(
        chart, "levo", "Grup-01", transit_pack=None)

    CIKTI.write_text(md, encoding="utf-8")
    duz = sadelestir(md)
    satirlar = md.split("\n")

    print("Yazildi: %s  (%d bayt)" % (CIKTI, len(md.encode())))
    print()

    # 1) Dort blok var mi
    dort_blok = ["Paket Sozlesmesi", "Veri Kapisi",
                 "Zorunlu Yuzey Denetimi", "Natal Karsi Kanit"]
    print("1) Dort blok:")
    for b in dort_blok:
        print("   %-26s %s" % (b, "VAR" if b in duz else "YOK"))
    print()

    # 2) Paket kimligi ve risk seviyesi
    print("2) Paket kimligi:")
    for anahtar in ["P08-HLT", "R3-ACUTE", "human_review", "İnsan"]:
        print("   %-26s %s" % (anahtar, "VAR" if anahtar in md else "YOK"))
    print()

    # 3) Bloklu dil gercekten yaziyor mu
    print("3) Bloklu dil (paket icinde acikca yasaklanmis olmali):")
    for ifade in ["hastalik teshisi", "teshis", "ilac", "tedavi"]:
        sayi = duz.lower().count(ifade)
        print("   %-26s gecis=%d" % (ifade, sayi))
    print()

    # 4) Organ/mekanizma tablosu
    print("4) Beden bolgesi tablosu:")
    basliklar = [l for l in satirlar if l.startswith("## ") or l.startswith("### ")]
    organ_basligi = [b for b in basliklar if "Beden" in b or "Mekanizma" in b]
    print("   baslik:", organ_basligi or "YOK")
    if organ_basligi:
        i = satirlar.index(organ_basligi[0])
        veri = [l for l in satirlar[i:i + 40]
                if l.startswith("| ") and "---" not in l]
        print("   satir sayisi:", len(veri))
        for l in veri[:3]:
            print("     ", l[:110])
    print()

    # 5) Tum basliklar
    print("5) Paket basliklari:")
    for b in [l for l in satirlar if l.startswith("## ")]:
        print("   ", b)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
