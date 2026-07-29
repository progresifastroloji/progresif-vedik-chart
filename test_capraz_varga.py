# -*- coding: utf-8 -*-
"""Capraz varga yamasi dogrulama testi.

Bozukluk kriteri: bir tablo blogunda ayirac satirindaki sutun sayisi ile
o blogun veri satirlarindaki sutun sayisi esit olmali.
"""

import json
import unicodedata
from pathlib import Path

import app

CHART_YOLU = "/tmp/tam.json"


def sadelestir(metin):
    return unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()


def sutun_sayisi(satir):
    return satir.count("|") - satir.count("\\|")


def bozuk_tablo_satirlari(metin):
    """Ayirac satirini referans alarak sutun sayisi tutmayanlari dondurur."""
    bozuk = []
    beklenen = None
    for satir in metin.split("\n"):
        if not satir.startswith("|"):
            beklenen = None
            continue
        if set(satir.replace("|", "").replace(" ", "")) <= {"-", ":"} and "-" in satir:
            beklenen = sutun_sayisi(satir)
            continue
        if beklenen is not None and sutun_sayisi(satir) != beklenen:
            bozuk.append(satir)
    return bozuk


def main():
    if not Path(CHART_YOLU).exists():
        print("HATA: %s yok." % CHART_YOLU)
        return 1

    chart = json.load(open(CHART_YOLU))

    hedefler = [
        ("career", app._build_career_analysis_data_package_markdown,
         ["D24 Chaturvimshamsha Uzmanlasma", "D2 Hora Kazanc"]),
        ("finance", app._build_finance_analysis_data_package_markdown,
         ["D10 Dashamsha Is Geliri"]),
        ("family", app._build_family_analysis_data_package_markdown,
         ["D9 Navamsha Genel Teyit"]),
    ]

    tum_ok = True
    for isim, fn, beklenenler in hedefler:
        md = fn(chart, "levo", "Grup-01", transit_pack=None)
        duz = sadelestir(md)

        eksik = [b for b in beklenenler if b not in duz]
        satirlar = md.split("\n")
        varga_basliklari = [l for l in satirlar if l.startswith("### D")]
        tablo_satirlari = [l for l in satirlar if l.startswith("| ")]
        bozuk = bozuk_tablo_satirlari(md)

        # yeni eklenen varga tablolari bos mu?
        bos_tablo = []
        for i, satir in enumerate(satirlar):
            if satir.startswith("### D") and "Destek Tablosu" in satir or \
               satir.startswith("### D") and "Teyit Tablosu" in satir:
                blok = satirlar[i:i + 30]
                veri = [l for l in blok if l.startswith("| ") and "---" not in l]
                if len(veri) < 3:
                    bos_tablo.append(satir)

        durum = "OK" if not eksik and not bozuk and not bos_tablo else "SORUN"
        tum_ok = tum_ok and durum == "OK"

        print("%-8s %-6s  bayt=%-7d tablo_satiri=%-4d bozuk=%d" % (
            isim, durum, len(md.encode()), len(tablo_satirlari), len(bozuk)))
        if eksik:
            print("         EKSIK BOLUM:", eksik)
        if bos_tablo:
            print("         BOS TABLO:", bos_tablo)
        for b in bozuk[:2]:
            print("         BOZUK SATIR:", b[:90])
        print("         varga tablolari:", varga_basliklari)
        print()

    print("SONUC:", "HEPSI OK" if tum_ok else "SORUN VAR")
    return 0 if tum_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
