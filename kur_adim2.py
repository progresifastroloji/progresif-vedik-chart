# -*- coding: utf-8 -*-
"""
Adim 2 kurulum betigi.

Yaptigi is:
  1. app.py yedegini alir -> app.py.yedek-adim2
  2. import satirini gunceller (2 yeni fonksiyon)
  3. Egitim paketine 2 yeni blok ekler (yuzey denetimi + natal karsi kanit)

Onkosul: topic_pack_contract.py v1.1.0 proje klasorunde olmali.

Geri alma:
  cp app.py.yedek-adim2 app.py
"""

import shutil
import sys
from pathlib import Path

APP = Path("app.py")
BACKUP = Path("app.py.yedek-adim2")

ESKI_IMPORT = ("from topic_pack_contract import "
               "package_contract_markdown, package_data_gate_markdown")
YENI_IMPORT = ("from topic_pack_contract import (\n"
               "    package_contract_markdown,\n"
               "    package_data_gate_markdown,\n"
               "    package_surface_audit_markdown,\n"
               "    package_counter_evidence_markdown,\n"
               ")")

ESKI_BLOK = '''        package_contract_markdown("P07-EDU"),
        "",
        package_data_gate_markdown(chart, "P07-EDU"),
        "",
        "## Kullanım Sınırı",'''

YENI_BLOK = '''        package_contract_markdown("P07-EDU"),
        "",
        package_data_gate_markdown(chart, "P07-EDU"),
        "",
        package_surface_audit_markdown(chart, "P07-EDU"),
        "",
        package_counter_evidence_markdown(chart, "P07-EDU"),
        "",
        "## Kullanım Sınırı",'''


def main():
    if not APP.exists():
        print("HATA: app.py bulunamadi. Dogru klasorde misin?")
        return 1

    mod = Path("topic_pack_contract.py")
    if not mod.exists():
        print("HATA: topic_pack_contract.py bulunamadi.")
        return 1

    src_mod = mod.read_text(encoding="utf-8")
    for fn in ("package_surface_audit_markdown", "package_counter_evidence_markdown"):
        if "def %s" % fn not in src_mod:
            print("HATA: topic_pack_contract.py eski surum (%s yok)." % fn)
            print("      Once yeni surumu kopyala.")
            return 1

    src = APP.read_text(encoding="utf-8")

    if "package_surface_audit_markdown" in src:
        print("BILGI: Adim 2 zaten uygulanmis. Degisiklik yapilmadi.")
        return 0

    for ad, capa in (("import", ESKI_IMPORT), ("blok", ESKI_BLOK)):
        adet = src.count(capa)
        if adet != 1:
            print("HATA: '%s' capasi %d kez bulundu, 1 bekleniyordu." % (ad, adet))
            print("      Adim 1 uygulanmis mi? Degisiklik yapilmadi.")
            return 1

    shutil.copy2(APP, BACKUP)
    print("1/3  yedek alindi -> %s" % BACKUP)

    src = src.replace(ESKI_IMPORT, YENI_IMPORT, 1)
    print("2/3  import guncellendi")

    src = src.replace(ESKI_BLOK, YENI_BLOK, 1)
    print("3/3  egitim paketine 2 blok eklendi")

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
