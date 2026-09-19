import os
import json
import tempfile
import unittest
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from flask import Flask

from digest import paid_routes, paid_store, paid_writer
from digest.paid_situation import (
    HOMEPAGE_CONTEXT_VERSION,
    HOMEPAGE_METHODOLOGY_VERSION,
    build_week_day_evidence,
)


def week_context():
    monday = date(2026, 9, 14)
    focuses = ("ilişki", "iş", "huzur", "çevre", "düzen", "yaratıcılık", "dinlenme")
    return {
        "schema_version": HOMEPAGE_CONTEXT_VERSION,
        "methodology_version": HOMEPAGE_METHODOLOGY_VERSION,
        "week_start": monday.isoformat(),
        "week_end": "2026-09-20",
        "days": [
            {
                "date": date.fromordinal(monday.toordinal() + index).isoformat(),
                "focus": focus,
                "eligible_domains": ([{"ilişki": "love", "iş": "work", "huzur": "family", "çevre": "friends"}[focus]] if focus in {"ilişki", "iş", "huzur", "çevre"} else []),
            }
            for index, focus in enumerate(focuses)
        ],
    }


def valid_output(context=None):
    context = context or week_context()
    terms = {
        "ilişki": ("Karşılıklı çabayı ölç ve sınırını koru.", "Yakın bir bağda söz ile davranış arasındaki fark görünür.", "Söylenene değil yapılanlara bak.", "Tek taraflı yükü üstlenme."),
        "iş": ("İş yükünü sıraya koy ve ana görevi bitir.", "Sorumluluklar netleştiğinde odağın daha sağlam kalır.", "Önce tek görevi tamamla.", "Aceleyle yeni taahhüt verme."),
        "huzur": ("Ev ve iç düzen bugün alan istiyor.", "Yakın çevrendeki ritim zihnini doğrudan etkiliyor.", "Kendine sakin bir köşe aç.", "Her çağrıya hemen dönme."),
        "çevre": ("Arkadaşlarınla açık ve seçici temas kur.", "Doğru bağlantı, ortak hedefini daha görünür yapar.", "İhtiyacını doğrudan söyle.", "Kalabalığa uyum için söz verme."),
        "düzen": ("Rutinini sadeleştir, yükünü dağıtma.", "Gün içindeki sorumluluklar düzen istediğini gösteriyor.", "Programını iki ana işe indir.", "Küçük işleri büyütme."),
        "yaratıcılık": ("Fikrini somutlaştır ve görünür kıl.", "Keyif aldığın üretim alanı bugün seni toparlar.", "Taslağı paylaşılacak hale getir.", "Onay bekleyip durma."),
        "dinlenme": ("Sessizliği seç, enerjini geri topla.", "Yoğunluk sonrası dinlenme alanı belirginleşiyor.", "Günü erken kapatmaya yer aç.", "Kendini açıklamak için yorulma."),
    }
    cards = []
    for evidence in context["days"]:
        message, reason, direction, notice = terms[evidence["focus"]]
        cards.append({
            "date": evidence["date"], "odak": evidence["focus"],
            "ana_mesaj": message, "neden": reason, "yon": direction,
            "dikkat": notice, "alanlar": evidence["eligible_domains"],
        })
    return {"motto": "Bu hafta netlik, seçici davranışla güç kazanır.", "days": cards}


class PaidHomepageDigestContractTests(unittest.TestCase):
    def test_week_contract_is_current(self):
        self.assertEqual(HOMEPAGE_CONTEXT_VERSION, "homepage_digest_context_v3")
        self.assertEqual(HOMEPAGE_METHODOLOGY_VERSION, "digest-methodology-v5")

    def test_writer_accepts_seven_evidence_bound_cards_and_direct_guidance(self):
        context = week_context()
        cleaned, error = paid_writer.validate(valid_output(context), context)
        self.assertIsNone(error)
        self.assertEqual(len(cleaned["days"]), 7)
        self.assertEqual(cleaned["days"][0]["yon"], "Söylenene değil yapılanlara bak.")

    def test_english_writer_receives_exact_labels_expected_by_validator(self):
        context = week_context()
        prompt = json.loads(paid_writer._user_text(context, "en"))
        self.assertEqual(
            [day["focus"] for day in prompt["week"]["days"]],
            [paid_writer.FOCUS_TRANSLATIONS[day["focus"]] for day in context["days"]],
        )
        self.assertEqual(context["days"][0]["focus"], "ilişki")
        self.assertIn("Copy each given focus exactly", prompt["output_instruction"])
        self.assertEqual(
            prompt["week"]["days"][0]["focus_anchors"],
            list(paid_writer.ENGLISH_FOCUS_TERMS["relationships"]),
        )
        self.assertNotIn("focus_anchors", context["days"][0])

    def test_writer_rejects_unproven_domain_future_claim_and_technical_leak(self):
        context = week_context()
        output = valid_output(context)
        output["days"][0]["alanlar"] = ["work"]
        self.assertEqual(paid_writer.validate(output, context)[1], "alan_kanitla_uyusmuyor")
        output = valid_output(context)
        output["days"][1]["ana_mesaj"] = "Yeni işin kesinleşecek, beklemeden kabul et."
        self.assertEqual(paid_writer.validate(output, context)[1], "kesin_gelecek_iddiasi")
        output = valid_output(context)
        output["days"][2]["neden"] = "Transit bilgisi evdeki düzenini açıklıyor."
        self.assertEqual(paid_writer.validate(output, context)[1], "teknik_terim_sizintisi")

    def test_unknown_birth_time_has_no_house_or_domain_evidence(self):
        chart = {
            "birth": {"time_declaration": "unknown"},
            "planets": [{"name": "Moon", "sign_index": 2}],
        }
        snapshot = {
            "date": "2026-09-14", "local_datetime": "2026-09-14T12:00:00+03:00",
            "planets": {"Moon": 4},
            "panchanga": {"status": "available", "paksha": "waxing", "vara_weekday": 0, "tithi_number": 2, "moon_nakshatra_index": 3},
        }
        evidence = build_week_day_evidence(chart, snapshot, reference_jd=2461297.0)
        self.assertEqual(evidence["data_quality"]["house_or_lagna_interpretation"], False)
        self.assertEqual(evidence["eligible_domains"], [])
        self.assertEqual(evidence["period"]["available"], False)

    def test_week_cache_is_scoped_by_owner_chart_week_language_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.environ.get("PAID_DIGEST_DB_PATH")
            os.environ["PAID_DIGEST_DB_PATH"] = os.path.join(tmp, "paid_digest.sqlite3")
            try:
                monday = date(2026, 9, 14)
                payload = valid_output()
                paid_store.set_homepage_week("user-a", "chart-a", payload, monday, "hash-a", "tr")
                self.assertEqual(paid_store.get_homepage_week("user-a", "chart-a", monday, "hash-a", "tr"), payload)
                self.assertIsNone(paid_store.get_homepage_week("user-a", "chart-a", monday, "hash-a", "en"))
                self.assertIsNone(paid_store.get_homepage_week("user-b", "chart-a", monday, "hash-a", "tr"))
                self.assertIsNone(paid_store.get_homepage_week("user-a", "chart-a", monday, "hash-b", "tr"))
                self.assertGreaterEqual(paid_store.delete_user("user-a"), 1)
                self.assertIsNone(paid_store.get_homepage_week("user-a", "chart-a", monday, "hash-a", "tr"))
            finally:
                if previous is None:
                    os.environ.pop("PAID_DIGEST_DB_PATH", None)
                else:
                    os.environ["PAID_DIGEST_DB_PATH"] = previous

    def test_route_generates_once_then_reuses_same_week_cache(self):
        app = Flask(__name__)
        app.register_blueprint(paid_routes.paid_digest_bp)
        context = week_context()
        payload = valid_output(context)
        current_hour = datetime(2026, 9, 16, 15, 0, tzinfo=ZoneInfo("Europe/Istanbul"))
        chart = {"meta": {"engine_version": "test"}}
        with patch.object(paid_routes, "_load_owned_chart", return_value=((chart, "chart-1", "profile-1", "user-1"), None)), \
                patch.object(paid_routes, "current_hour_ist", return_value=current_hour), \
                patch.object(paid_routes, "_load_weekly_snapshots", return_value=([{"date": day["date"]} for day in context["days"]], 0)), \
                patch.object(paid_routes, "build_personal_week_context", return_value=context), \
                patch.object(paid_routes, "_sha256", side_effect=["chart-hash", "snapshots-hash", "evidence-hash"] * 2), \
                patch.object(paid_routes.paid_store, "get_homepage_week", side_effect=[None, None, payload]), \
                patch.object(paid_routes.paid_store, "acquire_lock", return_value="owner"), \
                patch.object(paid_routes.paid_store, "release_lock"), \
                patch.object(paid_routes.paid_store, "set_homepage_week"), \
                patch.object(paid_routes.paid_writer, "generate", return_value=(payload, None)) as generate:
            first = app.test_client().post("/api/v2/pwa/digest/personal", json={})
            second = app.test_client().post("/api/v2/pwa/digest/personal", json={})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.get_json()["status"], "ready")
        self.assertEqual(second.get_json()["kaynak"], "onbellek")
        self.assertEqual(first.get_json()["week_start"], "2026-09-14")
        generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
