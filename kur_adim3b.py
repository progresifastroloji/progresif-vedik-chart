# -*- coding: utf-8 -*-
"""
Adim 3b: Kariyer paketine sozlesme bloklarini ekler.

Career builder digerlerinden farkli yapida: teknik icerigi
_expert_career_analysis_pack_markdown() yardimci fonksiyonuna delege
ediyor, "## Kullanım Sınırı" capasi yok. Bu yuzden Adim 3 betigi
(kur_adim3.py) bunu bilerek atladi.

Ekleme noktasi: "Sohbete ekle." satirindan sonra,
_expert_career_analysis_pack_markdown(...) cagrisindan once.

Geri alma:
  cp app.py.yedek-adim3b app.py
"""

import shutil
import sys
from pathlib import Path

APP = Path("app.py")
BACKUP = Path("app.py.yedek-adim3b")

ANCHOR = '''        "Sohbete ekle.",
        "",
        _expert_career_analysis_pack_markdown(chart, person_name, group_name),'''

NEW = '''        "Sohbete ekle.",
        "",
        package_contract_markdown("P03-CAR"),
        "",
        package_data_gate_markdown(chart, "P03-CAR"),
        "",
        package_surface_audit_markdown(chart, "P03-CAR"),
        "",
        package_counter_evidence_markdown(chart, "P03-CAR"),
        "",
        _expert_career_analysis_pack_markdown(chart, person_name, group_name),'''


def main():
    if not APP.exists():
        print("HATA: app.py bulunamadi.")
        return 1

    src = APP.read_text(encoding="utf-8")

    if 'package_contract_markdown("P03-CAR")' in src:
        print("BILGI: kariyer yamasi zaten uygulanmis. Degisiklik yapilmadi.")
        return 0

    adet = src.count(ANCHOR)
    if adet != 1:
        print("HATA: capa %d kez bulundu, 1 bekleniyordu." % adet)
        print("      app.py beklenenden farkli. Degisiklik yapilmadi.")
        return 1

    shutil.copy2(APP, BACKUP)
    print("1/2  yedek alindi -> %s" % BACKUP)

    src = src.replace(ANCHOR, NEW, 1)
    APP.write_text(src, encoding="utf-8")
    print("2/2  kariyer paketine 4 blok eklendi")

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
