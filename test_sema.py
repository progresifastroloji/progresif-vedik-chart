# -*- coding: utf-8 -*-
"""Sema v2.2.0 dogrulama testi.

Kabul etmeli : gecerli ornek, health status'u, sensitivity alani
Reddetmeli   : uydurma status, bos interpretation_limit,
               eksik timing_windows, readiness statusu
"""

import json
from pathlib import Path

SEMA = Path.home() / "Downloads" / "analysis_output_schema_v2.json"


def temel():
    return {
        "topic_pack": "P08-HLT",
        "question_type": "saglik stres oruntusu",
        "risk_level": "R3-ACUTE",
        "human_review_required": True,
        "data_gate": {"birth_time_confidence": "rectified", "passed": True},
        "technical_factors": [
            {"surface": "Saturn Shadbala", "value": "210.59"}
        ],
        "mandatory_surfaces_covered": {
            "required": ["Lagna/lord"], "covered": ["Lagna/lord"], "missing": []
        },
        "main_evidence": [{
            "claim": "Lagna lordu 8. evde",
            "evidence_id": "RUL-T03-0015",
            "status": "ACTIVE",
            "school": "PARASHARI",
        }],
        "counter_evidence": [{
            "claim": "Saturn dusman burcta",
            "evidence_id": "RUL-INT-0013",
            "status": "ACTIVE",
            "school": "PARASHARI",
        }],
        "thematic_core": [{"name": "Tasiyici yapi yuku", "mechanism": "kuruma"}],
        "confidence": {
            "data": "medium", "source": "medium", "method": "medium",
            "overall": "medium", "rationale": "rektifikasyon kaynagi belirtilmemis",
        },
        "blocked_claims_check": {"checked": True, "violations": []},
        "citations": ["RUL-T03-0015"],
        "limits": ["teshis uretmez"],
        "timing_windows": [{
            "start_date": "2020-01-01",
            "end_date": "2020-01-26",
            "dasha_path": "Saturn > Saturn > Rahu > Rahu",
            "sensitivity": "sookshma",
            "status": "technical_candidate_not_medical_prediction",
            "interpretation_limit":
                "does_not_establish_a_medical_emergency_diagnosis_or_body_system",
        }],
    }


def main():
    try:
        import jsonschema
    except ImportError:
        print("jsonschema kurulu degil. Kur:")
        print("  .venv/bin/pip install jsonschema")
        return 1

    sema = json.loads(SEMA.read_text(encoding="utf-8"))
    print("Sema surumu:", sema.get("version"))
    print()

    senaryolar = []

    senaryolar.append(("saglik penceresi (health status + sensitivity)",
                       temel(), True))

    d = temel()
    d["timing_windows"][0]["status"] = "technical_candidate_not_prediction"
    d["timing_windows"][0].pop("sensitivity")
    senaryolar.append(("kariyer penceresi (eski status, sensitivity yok)", d, True))

    d = temel()
    d["timing_windows"][0]["status"] = "kesin_hastalik_penceresi"
    senaryolar.append(("uydurma status", d, False))

    d = temel()
    d["timing_windows"][0]["status"] = "starter_candidate_inventory"
    senaryolar.append(("readiness statusu (zamanlama degil)", d, False))

    d = temel()
    d["timing_windows"][0]["interpretation_limit"] = ""
    senaryolar.append(("bos interpretation_limit", d, False))

    d = temel()
    d["timing_windows"][0].pop("interpretation_limit")
    senaryolar.append(("eksik interpretation_limit", d, False))

    d = temel()
    d.pop("timing_windows")
    senaryolar.append(("timing_windows alani yok", d, False))

    d = temel()
    d["timing_windows"][0]["sensitivity"] = "gunluk"
    senaryolar.append(("uydurma sensitivity", d, False))

    d = temel()
    d["timing_windows"][0]["Hassasiyet"] = "sookshma"
    senaryolar.append(("taninmayan ek alan", d, False))

    hata_sayisi = 0
    for ad, veri, beklenen_gecer in senaryolar:
        try:
            jsonschema.validate(veri, sema)
            gecti = True
            mesaj = ""
        except jsonschema.ValidationError as e:
            gecti = False
            mesaj = e.message[:60]

        dogru = gecti == beklenen_gecer
        if not dogru:
            hata_sayisi += 1
        print("%-45s %-8s %s" % (
            ad,
            "KABUL" if gecti else "RED",
            "OK" if dogru else "!!! BEKLENEN: %s" % (
                "KABUL" if beklenen_gecer else "RED"),
        ))
        if not gecti and beklenen_gecer:
            print("      sebep:", mesaj)

    print()
    print("SONUC:", "HEPSI OK" if hata_sayisi == 0 else "%d HATA" % hata_sayisi)
    return 0 if hata_sayisi == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
