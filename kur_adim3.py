# -*- coding: utf-8 -*-
"""
Adim 3: Sozlesme bloklarini kalan paketlere yayar.

Her builder icin:
  1. Fonksiyon govdesini bulur
  2. Icindeki ilk '"## Kullanım Sınırı",' satirini bulur
  3. Oradan once 4 blok cagrisi ekler

Emin olamadigi builder'i ATLAR ve raporlar. Tahmin yapmaz.

Geri alma:
  cp app.py.yedek-adim3 app.py
"""

import re
import shutil
import sys
from pathlib import Path

APP = Path("app.py")
BACKUP = Path("app.py.yedek-adim3")

# (fonksiyon adi, paket kimligi)
HEDEFLER = [
    ("_build_character_analysis_data_package_markdown",    "GENERAL"),
    ("_build_health_analysis_data_package_markdown",       "P08-HLT"),
    ("_build_family_analysis_data_package_markdown",       "P06-CHI"),
    ("_build_relocation_analysis_data_package_markdown",   "P05-PRO"),
    ("_build_finance_analysis_data_package_markdown",      "P04-WEA"),
    ("_build_relationship_analysis_data_package_markdown", "P01-MAR"),
    ("_build_spiritual_analysis_data_package_markdown",    "P10-SPI"),
    ("_build_legal_analysis_data_package_markdown",        "P09-LIT"),
    ("_build_varshaphala_analysis_data_package_markdown",  "P11-TIM"),
]

ANCHOR = '        "## Kullanım Sınırı",'


def bloklar(pack_id):
    return (
        '        package_contract_markdown("%s"),\n'
        '        "",\n'
        '        package_data_gate_markdown(chart, "%s"),\n'
        '        "",\n'
        '        package_surface_audit_markdown(chart, "%s"),\n'
        '        "",\n'
        '        package_counter_evidence_markdown(chart, "%s"),\n'
        '        "",\n'
    ) % (pack_id, pack_id, pack_id, pack_id)


def fonksiyon_araligi(src, isim):
    """Fonksiyonun baslangic ve bitis konumunu bulur."""
    m = re.search(r"^def %s\(" % re.escape(isim), src, re.M)
    if not m:
        return None
    bas = m.start()
    m2 = re.search(r"^def ", src[m.end():], re.M)
    son = m.end() + m2.start() if m2 else len(src)
    return (bas, son)


def main():
    if not APP.exists():
        print("HATA: app.py bulunamadi.")
        return 1

    src = APP.read_text(encoding="utf-8")

    if "package_surface_audit_markdown" not in src:
        print("HATA: Adim 2 uygulanmamis. Once kur_adim2.py calistir.")
        return 1

    # zaten yamali olanlari tespit et
    yapilacak, atlanan, zaten = [], [], []
    for isim, pack_id in HEDEFLER:
        aralik = fonksiyon_araligi(src, isim)
        if not aralik:
            atlanan.append((isim, "fonksiyon bulunamadi"))
            continue
        govde = src[aralik[0]:aralik[1]]
        if "package_contract_markdown" in govde:
            zaten.append(isim)
            continue
        if govde.count(ANCHOR) != 1:
            atlanan.append((isim, "capa %d kez bulundu" % govde.count(ANCHOR)))
            continue
        yapilacak.append((isim, pack_id, aralik))

    print("Durum:")
    print("  yamalanacak : %d" % len(yapilacak))
    print("  zaten yamali: %d" % len(zaten))
    print("  atlanan     : %d" % len(atlanan))
    for isim, sebep in atlanan:
        print("     - %s (%s)" % (isim.replace("_build_", "").replace(
            "_analysis_data_package_markdown", ""), sebep))
    print("")

    if not yapilacak:
        print("Yapilacak is yok.")
        return 0

    shutil.copy2(APP, BACKUP)
    print("yedek alindi -> %s" % BACKUP)
    print("")

    # sondan basa dogru yamala ki konumlar kaymasin
    yapilacak.sort(key=lambda x: -x[2][0])
    for isim, pack_id, (bas, son) in yapilacak:
        govde = src[bas:son]
        yeni_govde = govde.replace(ANCHOR, bloklar(pack_id) + ANCHOR, 1)
        src = src[:bas] + yeni_govde + src[son:]
        kisa = isim.replace("_build_", "").replace(
            "_analysis_data_package_markdown", "")
        print("  %-16s -> %s" % (kisa, pack_id))

    APP.write_text(src, encoding="utf-8")

    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
        print("")
        print("Syntax kontrolu: OK")
    except py_compile.PyCompileError as exc:
        print("")
        print("HATA: syntax bozuldu, geri aliniyor...")
        shutil.copy2(BACKUP, APP)
        print("Geri alindi. Hata: %s" % exc)
        return 1

    print("")
    print("TAMAM. Simdi testi calistir:")
    print("  .venv/bin/python -m unittest tests.test_api_v2 2>&1 | tail -5")
    return 0


if __name__ == "__main__":
    sys.exit(main())
