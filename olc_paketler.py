# -*- coding: utf-8 -*-
"""
Paket uretim suresi olcumu.

Hicbir dosyaya yazmaz. Sadece _build_* fonksiyonlarini calistirip
her birinin kac saniye surdugunu ve kac bayt urettigini basar.

Kullanim:
    cd ~/Documents/progresifastrolog/progresif-vedik-chart
    .venv/bin/python olc_paketler.py
"""

import json
import time
from pathlib import Path

CHART_JSON = Path("/tmp/tam.json")

if not CHART_JSON.exists():
    print("HATA: /tmp/tam.json yok. Once chart/full ciktisini oraya kaydet.")
    raise SystemExit(1)

print("chart yukleniyor...")
t0 = time.perf_counter()
chart = json.loads(CHART_JSON.read_text(encoding="utf-8"))
print("  %.2f sn, %.1f MB" % (time.perf_counter() - t0, CHART_JSON.stat().st_size / 1e6))

print("app.py import ediliyor...")
t0 = time.perf_counter()
import app
print("  %.2f sn" % (time.perf_counter() - t0))

BUILDERS = [
    ("career",       "_build_career_analysis_data_package_markdown"),
    ("health",       "_build_health_analysis_data_package_markdown"),
    ("family",       "_build_family_analysis_data_package_markdown"),
    ("education",    "_build_education_analysis_data_package_markdown"),
    ("relocation",   "_build_relocation_analysis_data_package_markdown"),
    ("finance",      "_build_finance_analysis_data_package_markdown"),
    ("relationship", "_build_relationship_analysis_data_package_markdown"),
    ("character",    "_build_character_analysis_data_package_markdown"),
    ("spiritual",    "_build_spiritual_analysis_data_package_markdown"),
    ("varshaphala",  "_build_varshaphala_analysis_data_package_markdown"),
    ("legal",        "_build_legal_analysis_data_package_markdown"),
    ("planets",      "_build_planet_role_activation_package_markdown"),
    ("session",      "_build_session_preparation_package_markdown"),
]

print("")
print("%-14s %9s %10s" % ("paket", "sure(sn)", "boyut(KB)"))
print("-" * 36)

results = []
for label, fname in BUILDERS:
    fn = getattr(app, fname, None)
    if fn is None:
        print("%-14s %9s %10s" % (label, "YOK", "-"))
        continue
    out = None
    elapsed = None
    err = None
    try:
        t0 = time.perf_counter()
        out = fn(chart, "levo", "Grup-01", transit_pack=None)
        elapsed = time.perf_counter() - t0
    except TypeError:
        try:
            t0 = time.perf_counter()
            out = fn(chart, "levo", "Grup-01")
            elapsed = time.perf_counter() - t0
        except Exception as exc:
            err = type(exc).__name__
    except Exception as exc:
        err = type(exc).__name__

    if out is not None:
        size = len(out.encode("utf-8")) / 1024
        results.append((label, elapsed, size))
        print("%-14s %9.2f %10.1f" % (label, elapsed, size))
    else:
        print("%-14s %9s  %s" % (label, "HATA", err))

print("-" * 36)
if results:
    total = sum(r[1] for r in results)
    print("%-14s %9.2f %10.1f" % ("TOPLAM", total, sum(r[2] for r in results)))
    print("")
    results.sort(key=lambda r: -r[1])
    print("En yavas ucu:")
    for label, elapsed, _ in results[:3]:
        print("  %-14s %6.2f sn  (%%%.0f)" % (label, elapsed, 100 * elapsed / total))
