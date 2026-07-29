# -*- coding: utf-8 -*-
"""
Capraz varga bosluklarini kapatir.

career  -> D24 (egitim/uzmanlasma alt konusu) + D2 (kazanc) destek tablosu
finance -> D10 (is geliri) destek tablosu
family  -> D9  (genel teyit) destek tablosu

Veri motorda zaten hesapli (VARGA_NAMES icinde 14 varga var); bu betik
yalniz mevcut _expert_varga_rows() ciktisini ilgili pakete yazar.
Hesap mantigi degismez. Idempotenttir: ikinci kez calistirilirsa dokunmaz.
"""

import ast
import shutil
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent / "app.py"
YEDEK = APP.with_suffix(".py.yedek-capraz-varga")

# (isim, aranan_metin, eklenecek_metin, imza)
YAMALAR = [
    (
        "career",
        '        _expert_career_analysis_pack_markdown(chart, person_name, group_name),\n'
        '        "",\n'
        '        "## Konu Analiz Özeti",\n',

        '        _expert_career_analysis_pack_markdown(chart, person_name, group_name),\n'
        '        "",\n'
        '        "## Kariyer Çapraz Varga Desteği",\n'
        '        "",\n'
        '        "- D24 ve D2 kariyer için ana varga değildir; D10 ile çelişirse D10 esas alınır.",\n'
        '        "- D24 uzmanlaşma/eğitim alt konusunu, D2 kazanç bağlamını teyit amaçlıdır.",\n'
        '        "- Her ikisi de düşük yorum güvenlidir; tek başına hüküm kurulamaz.",\n'
        '        "",\n'
        '        "### D24 Chaturvimshamsha Uzmanlaşma Destek Tablosu",\n'
        '        "",\n'
        '        _markdown_table(["Nokta", "Burç", "Derece"], _expert_varga_rows(chart, "D24")),\n'
        '        "",\n'
        '        "### D2 Hora Kazanç Destek Tablosu",\n'
        '        "",\n'
        '        _markdown_table(["Nokta", "Burç", "Derece"], _expert_varga_rows(chart, "D2")),\n'
        '        "",\n'
        '        "## Konu Analiz Özeti",\n',

        "## Kariyer Çapraz Varga Desteği",
    ),
    (
        "finance",
        '        "### D4 Mülk Destek Tablosu", "",\n'
        '        _markdown_table(["Nokta", "Burç", "Derece"], _expert_varga_rows(chart, "D4")),\n'
        '        "",\n'
        '        _finance_timing_markdown(life_period), "",\n',

        '        "### D4 Mülk Destek Tablosu", "",\n'
        '        _markdown_table(["Nokta", "Burç", "Derece"], _expert_varga_rows(chart, "D4")),\n'
        '        "",\n'
        '        "### D10 Dashamsha İş Geliri Destek Tablosu", "",\n'
        '        "- D10 finans için ana varga değildir; D2 ile çelişirse D2 esas alınır.",\n'
        '        "- Gelirin iş/meslek kaynaklı olup olmadığını ayırt etmek için destek kanıtıdır.",\n'
        '        "- Düşük yorum güvenlidir; tek başına gelir hükmü kurulamaz.",\n'
        '        "",\n'
        '        _markdown_table(["Nokta", "Burç", "Derece"], _expert_varga_rows(chart, "D10")),\n'
        '        "",\n'
        '        _finance_timing_markdown(life_period), "",\n',

        "### D10 Dashamsha İş Geliri Destek Tablosu",
    ),
    (
        "family",
        '        "### D4 Chaturthamsha Destek Tablosu",\n'
        '        "",\n'
        '        _markdown_table(["Nokta", "Burç", "Derece"], _expert_varga_rows(chart, "D4")),\n'
        '        "",\n'
        '        "## Aktif Vimshottari Aile Bağlantısı",\n',

        '        "### D4 Chaturthamsha Destek Tablosu",\n'
        '        "",\n'
        '        _markdown_table(["Nokta", "Burç", "Derece"], _expert_varga_rows(chart, "D4")),\n'
        '        "",\n'
        '        "### D9 Navamsha Genel Teyit Tablosu",\n'
        '        "",\n'
        '        "- D9 aile için ana varga değildir; D7/D12 ile çelişirse D7/D12 esas alınır.",\n'
        '        "- Haritanın genel dayanıklılığını teyit amaçlı okunur.",\n'
        '        "- Çocuk sayısı, cinsiyeti veya gebelik sonucu bu tablodan çıkarılamaz.",\n'
        '        "",\n'
        '        _markdown_table(["Nokta", "Burç", "Derece"], _expert_varga_rows(chart, "D9")),\n'
        '        "",\n'
        '        "## Aktif Vimshottari Aile Bağlantısı",\n',

        "### D9 Navamsha Genel Teyit Tablosu",
    ),
]


def main():
    if not APP.exists():
        print("HATA: app.py bulunamadi:", APP)
        return 1

    metin = APP.read_text(encoding="utf-8")

    yamalanacak, zaten, bulunamadi = [], [], []
    for isim, ara, yeni, imza in YAMALAR:
        if imza in metin:
            zaten.append(isim)
        elif metin.count(ara) == 1:
            yamalanacak.append(isim)
        else:
            bulunamadi.append((isim, metin.count(ara)))

    print("Durum:")
    print("  yamalanacak : %d %s" % (len(yamalanacak), yamalanacak or ""))
    print("  zaten yamali: %d %s" % (len(zaten), zaten or ""))
    print("  bulunamadi  : %d %s" % (len(bulunamadi), bulunamadi or ""))
    print()

    if bulunamadi:
        print("DURDURULDU. Yukaridaki paketlerde beklenen kod bloklari")
        print("tam olarak 1 kez bulunamadi. Tahmin yapilmadi, hicbir sey degistirilmedi.")
        return 2

    if not yamalanacak:
        print("Yapilacak is yok; tum bloklar zaten uygulanmis.")
        return 0

    shutil.copy2(APP, YEDEK)
    print("yedek alindi ->", YEDEK.name)
    print()

    for isim, ara, yeni, imza in YAMALAR:
        if imza in metin:
            continue
        metin = metin.replace(ara, yeni, 1)
        print("  %-8s -> capraz varga destek tablosu eklendi" % isim)

    try:
        ast.parse(metin)
    except SyntaxError as hata:
        print()
        print("SYNTAX HATASI, yazilmadi:", hata)
        return 3

    APP.write_text(metin, encoding="utf-8")
    print()
    print("Syntax kontrolu: OK")
    print()
    print("TAMAM. Simdi testi calistir:")
    print("  .venv/bin/python -m unittest tests.test_api_v2 2>&1 | tail -5")
    return 0


if __name__ == "__main__":
    sys.exit(main())
