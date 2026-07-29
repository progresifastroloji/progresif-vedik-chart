# -*- coding: utf-8 -*-
"""
Hiz yamasi: life_period_analysis tek kez hesaplansin.

Sorun:
  11 paket builder'i _build_life_period_analysis_for_chart(chart) cagiriyor.
  Tek cagri 4.71 sn suruyor ve 23 anahtarin HEPSINI uretiyor.
  Ayni sonuc 11 kez hesaplaniyor -> ~49 sn.

Cozum:
  _save_analysis_data_packages basinda bir kez hesapla, chart'a yaz.
  Builder'lar kendi kontrolunde bulur ve yeniden hesaplamaz.
  Fonksiyon bitince chart eski haline dondurulur (yan etki yok).

Beklenen: ~49 sn -> ~6 sn

Geri alma:
  cp app.py.yedek-hiz app.py
"""

import shutil
import sys
from pathlib import Path

APP = Path("app.py")
BACKUP = Path("app.py.yedek-hiz")

ANCHOR_BASLANGIC = '''    active_transit_pack = transit_pack
    if not active_transit_pack:
        active_transit_pack = _latest_saved_transit_pack(
            group_name,
            person_name,
            "three_month",
        )
    career_path = _save_career_analysis_data_package('''

YENI_BASLANGIC = '''    active_transit_pack = transit_pack
    if not active_transit_pack:
        active_transit_pack = _latest_saved_transit_pack(
            group_name,
            person_name,
            "three_month",
        )
    # --- hiz yamasi: life_period_analysis tek kez hesaplanir ---
    _lp_yedek = chart.get("life_period_analysis")
    _lp_mevcut = _lp_yedek or {}
    if not _lp_mevcut.get("education_timing_evidence_v1"):
        chart["life_period_analysis"] = _build_life_period_analysis_for_chart(chart)
    # --- hiz yamasi sonu ---
    career_path = _save_career_analysis_data_package('''

ANCHOR_BITIS = '''    return {
        "career": career_path,'''

YENI_BITIS = '''    # --- hiz yamasi: chart eski haline dondurulur ---
    if _lp_yedek is None:
        chart.pop("life_period_analysis", None)
    else:
        chart["life_period_analysis"] = _lp_yedek
    # --- hiz yamasi sonu ---
    return {
        "career": career_path,'''


def main():
    if not APP.exists():
        print("HATA: app.py bulunamadi. Dogru klasorde misin?")
        return 1

    src = APP.read_text(encoding="utf-8")

    if "hiz yamasi" in src:
        print("BILGI: hiz yamasi zaten uygulanmis. Degisiklik yapilmadi.")
        return 0

    for ad, capa in (("baslangic", ANCHOR_BASLANGIC), ("bitis", ANCHOR_BITIS)):
        adet = src.count(capa)
        if adet != 1:
            print("HATA: '%s' capasi %d kez bulundu, 1 bekleniyordu." % (ad, adet))
            print("      app.py beklenenden farkli. Degisiklik yapilmadi.")
            return 1

    shutil.copy2(APP, BACKUP)
    print("1/3  yedek alindi -> %s" % BACKUP)

    src = src.replace(ANCHOR_BASLANGIC, YENI_BASLANGIC, 1)
    print("2/3  onbellek baslangici eklendi")

    src = src.replace(ANCHOR_BITIS, YENI_BITIS, 1)
    print("3/3  chart geri yukleme eklendi")

    APP.write_text(src, encoding="utf-8")

    # syntax kontrolu
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
    print("TAMAM. Simdi olcumu tekrar calistir:")
    print("  .venv/bin/python olc_paketler.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
