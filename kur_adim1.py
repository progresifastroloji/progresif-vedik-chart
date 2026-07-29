# -*- coding: utf-8 -*-
"""
Adim 1 kurulum betigi.

Yaptigi is:
  1. app.py yedegini alir  -> app.py.yedek-adim1
  2. import satirini ekler
  3. YALNIZ egitim paketine iki blok ekler (referans paket)

Baska hicbir sey degistirmez. Geri almak icin:
  cp app.py.yedek-adim1 app.py
"""

import re
import shutil
import sys
from pathlib import Path

APP = Path("app.py")
BACKUP = Path("app.py.yedek-adim1")

IMPORT_LINE = "from topic_pack_contract import package_contract_markdown, package_data_gate_markdown\n"

ANCHOR_CONTRACT = '''        "## Kullanım Sınırı",
        "",
        "- Bu paket teknik eğitim ve uzmanlaşma kanıtı içerir; başarı veya sonuç tahmini üretmez."'''

NEW_CONTRACT = '''        package_contract_markdown("P07-EDU"),
        "",
        package_data_gate_markdown(chart, "P07-EDU"),
        "",
        "## Kullanım Sınırı",
        "",
        "- Bu paket teknik eğitim ve uzmanlaşma kanıtı içerir; başarı veya sonuç tahmini üretmez."'''


def main():
    if not APP.exists():
        print("HATA: app.py bulunamadi. Dogru klasorde misin?")
        return 1

    if not Path("topic_pack_contract.py").exists():
        print("HATA: topic_pack_contract.py bulunamadi. Once onu olustur.")
        return 1

    src = APP.read_text(encoding="utf-8")

    if "topic_pack_contract" in src:
        print("BILGI: yama zaten uygulanmis. Degisiklik yapilmadi.")
        return 0

    if ANCHOR_CONTRACT not in src:
        print("HATA: egitim paketindeki capa metni bulunamadi.")
        print("      app.py beklenenden farkli. Degisiklik yapilmadi.")
        return 1

    if src.count(ANCHOR_CONTRACT) != 1:
        print("HATA: capa metni %d kez gecti, 1 bekleniyordu." % src.count(ANCHOR_CONTRACT))
        return 1

    shutil.copy2(APP, BACKUP)
    print("1/3  yedek alindi -> %s" % BACKUP)

    # import satirini son 'import' veya 'from ... import' blogunun ardina koy
    lines = src.split("\n")
    last_import = 0
    for i, line in enumerate(lines[:400]):
        if re.match(r"^(import |from )\S", line):
            last_import = i
    lines.insert(last_import + 1, IMPORT_LINE.rstrip("\n"))
    src = "\n".join(lines)
    print("2/3  import eklendi (satir %d)" % (last_import + 2))

    src = src.replace(ANCHOR_CONTRACT, NEW_CONTRACT, 1)
    print("3/3  egitim paketine 2 blok eklendi")

    APP.write_text(src, encoding="utf-8")
    print("")
    print("TAMAM. Simdi testi calistir:")
    print("  .venv/bin/python -m unittest tests.test_api_v2 2>&1 | tail -5")
    return 0


if __name__ == "__main__":
    sys.exit(main())
