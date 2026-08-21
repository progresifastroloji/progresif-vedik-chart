"""Gecici deneme scripti. Faz 1 dogrulamasi icin.

v1'den fark: artik katmana gore dogru sayida snapshot uretiyor
(daily=1, weekly=7, monthly=~28-31), boylece ana_tema haftalik/aylik
icin kendi mantigini kullanabiliyor.

Calistirma:
    cd /Users/leventkalayci/Documents/progresifastrolog/progresif-vedik-chart
    source .venv/bin/activate
    python3 -m digest.deneme_paid_situation

Isini gordukten sonra silinebilir; hicbir mevcut dosyayi degistirmez,
hicbir routea baglanmaz.
"""

import json
from datetime import date

from digest.paid_situation import build_paid_situation
from digest.situation import planet_signs, required_days

CHART_PATH = "VEDIK_CHART_API_BILGI_PAKETI/ornek_set/ham_json/chart_full_response.json"


def _snaps_for(katman, d):
    gunler = required_days(katman, d)
    return [planet_signs(g) for g in gunler]


def main():
    with open(CHART_PATH) as f:
        chart = json.load(f)

    today = date.today()
    print("Bugun:", today.isoformat())

    # Aylik ~30 gun calculate_chart cagirir, biraz surer; bir kez uretip
    # katmanlar arasinda paylasalim.
    snap_cache = {}
    for katman in ("daily", "weekly", "monthly"):
        snap_cache[katman] = _snaps_for(katman, today)
    print("Snapshot sayilari:", {k: len(v) for k, v in snap_cache.items()})
    print()

    for lord in ("Jupiter", "Saturn", "Venus", "Rahu"):
        for katman in ("daily", "weekly", "monthly"):
            paket = build_paid_situation(chart, katman, lord, snap_cache[katman])
            print("--- lord=%s katman=%s ---" % (lord, katman))
            print(json.dumps(paket, indent=2, ensure_ascii=False))
            print()


if __name__ == "__main__":
    main()
