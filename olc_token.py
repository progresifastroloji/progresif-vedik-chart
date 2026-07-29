# -*- coding: utf-8 -*-
"""Gemini'ye yuklenen dosyalarin gercek token maliyetini olcer.

Token tahmini: Turkce metin icin ~3.2 karakter/token (Ingilizce ~4).
Kesin deger degil, +/- %15 sapma normal.
"""

from pathlib import Path

DL = Path.home() / "Downloads"

# Agent Studio'ya yuklenen / yuklenebilecek dosyalar
ADAYLAR = [
    "SYSTEM_METHODOLOGY.txt",
    "SYSTEM_METHODOLOGY.md",
    "rules.txt",
    "rules.csv",
    "terms.txt",
    "terms.csv",
    "schema.txt",
    "analysis_output_schema_v2.json",
    "egitim.txt",
    "egitim.md",
    "saglik.txt",
    "saglik.md",
    "TEST_PROTOKOLU.md",
    "ASAMA_PROMPTLARI_v2.md",
]

KARAKTER_BASINA_TOKEN = 3.2


def olc(yol):
    try:
        metin = yol.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    return {
        "bayt": yol.stat().st_size,
        "karakter": len(metin),
        "satir": metin.count("\n") + 1,
        "token": int(len(metin) / KARAKTER_BASINA_TOKEN),
    }


def main():
    print("=" * 78)
    print("%-34s %10s %10s %10s" % ("DOSYA", "KARAKTER", "SATIR", "~TOKEN"))
    print("=" * 78)

    bulunan = []
    for ad in ADAYLAR:
        yol = DL / ad
        if not yol.exists():
            continue
        o = olc(yol)
        if o is None:
            continue
        bulunan.append((ad, o))
        print("%-34s %10d %10d %10d" % (ad, o["karakter"], o["satir"], o["token"]))

    print()
    eksik = [a for a in ADAYLAR if not (DL / a).exists()]
    if eksik:
        print("Downloads'ta bulunamayan:", ", ".join(eksik))
        print()

    # Agent Studio'ya gercekte yuklu olanlar (ekran goruntusunden)
    yuklu = ["rules.txt", "terms.txt", "egitim.txt", "schema.txt"]
    print("=" * 78)
    print("SU AN AGENT STUDIO'DA YUKLU OLANLAR")
    print("=" * 78)
    toplam = 0
    for ad in yuklu:
        yol = DL / ad
        if yol.exists():
            o = olc(yol)
            toplam += o["token"]
            print("%-34s %10d token" % (ad, o["token"]))
        else:
            print("%-34s %10s" % (ad, "BULUNAMADI"))
    print("-" * 78)
    print("%-34s %10d token" % ("TOPLAM (dosyalar)", toplam))
    print()
    print("Not: System instructions (metodoloji) da her turda gonderiliyor.")
    print("Ekranda gorulen 142.769 token bu dosyalar + system instructions")
    print("+ sohbet gecmisinin toplamidir.")
    print()

    # Senaryo karsilastirmasi
    print("=" * 78)
    print("SENARYO: SAGLIK TESTI ICIN NE YUKLENMELI")
    print("=" * 78)
    senaryolar = [
        ("Simdiki hali (egitim + saglik birlikte)",
         ["rules.txt", "terms.txt", "egitim.txt", "schema.txt", "saglik.txt"]),
        ("Sadece saglik (egitim.txt kaldirilir)",
         ["rules.txt", "terms.txt", "schema.txt", "saglik.txt"]),
        ("Saglik + kucultulmus rules (varsayim: %40)",
         ["terms.txt", "schema.txt", "saglik.txt"]),
    ]
    for ad, dosyalar in senaryolar:
        t = 0
        for d in dosyalar:
            yol = DL / d
            if yol.exists():
                t += olc(yol)["token"]
        print("%-46s %10d token" % (ad, t))
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
