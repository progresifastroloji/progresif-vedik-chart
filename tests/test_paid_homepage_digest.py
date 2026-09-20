import json
import os
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
        "ilişki": "İlişkilerde karşılıklı çabayı daha dikkatle ölçmek isteyebilirsin. Yakın bir bağda söylenenle yapılan arasındaki fark bugün daha görünür olabilir; bunu hemen büyütmek yerine sınırını sakin biçimde koru. İhtiyacını açık söyle, fakat tek taraflı yükü üstlenerek dengeyi kendi aleyhine bozma.",
        "iş": "İş yükün içinde hangi görevin gerçekten öncelikli olduğunu ayırt etmek bugün daha kolaylaşır. Sorumlulukların netleşmesi, odağını dağıtan küçük talepleri elemeni sağlayabilir. Önce ana işi tamamla; hızlı görünmek için yeni bir yük üstlenmek yerine mevcut düzenini koru.",
        "huzur": "Ev ve iç düzen, günün geri kalanını nasıl taşıdığını doğrudan etkileyebilir. Yakın çevrendeki ritim yoğunlaştığında kendine kısa bir sakin alan açmak, duygularını daha rahat duymanı sağlar. Her çağrıya hemen dönmek yerine kendi hızını belirlemeyi dene.",
        "çevre": "Arkadaşların ve içinde bulunduğun çevre bugün hangi bağların seni gerçekten desteklediğini gösterebilir. Ortak hedeflerin konuşulduğu bir yerde ihtiyacını doğrudan dile getirmen ilişkiyi netleştirir. Kalabalığa uyum sağlamak için istemediğin bir söz vermekten kaçın.",
        "düzen": "Günün sorumlulukları, rutinin içinde daha sade bir düzen kurma ihtiyacını öne çıkarabilir. Programını iki ana işe indirmek, zihnindeki dağınıklığı azaltır ve yaptığın işe daha sağlam dönmeni sağlar. Küçük ayrıntıları büyütmek yerine yapılabilir bir sıraya bağlı kal.",
        "yaratıcılık": "Fikrini somutlaştırmak ve keyif aldığın üretim alanına biraz daha yer açmak bugün iyi gelebilir. İçinde tuttuğun taslağı görünür hale getirdiğinde hem hevesin hem de yönün netleşir. Onay bekleyerek ertelemek yerine küçük ama tamamlanmış bir adım at.",
        "dinlenme": "Yoğunluğun ardından sessizliğe ve dinlenmeye ayırdığın alan bugün daha değerli hissedilebilir. Kendini sürekli açıklamak ya da yetişmek zorunda bırakmadan günün temposunu yavaşlatmak, gücünü toplamana yardım eder. Günü erken kapatmaya yer aç ve geleceği çözmeye çalışma.",
    }
    cards = []
    for evidence in context["days"]:
        cards.append({
            "date": evidence["date"], "odak": evidence["focus"],
            "yorum": terms[evidence["focus"]], "alanlar": evidence["eligible_domains"],
        })
    return {"motto": "Bu hafta netlik, seçici davranışla güç kazanır.", "days": cards}


class PaidHomepageDigestContractTests(unittest.TestCase):
    def test_week_contract_is_current(self):
        self.assertEqual(HOMEPAGE_CONTEXT_VERSION, "homepage_digest_context_v4")
        self.assertEqual(HOMEPAGE_METHODOLOGY_VERSION, "digest-methodology-v6")

    def test_writer_accepts_seven_evidence_bound_cards_and_direct_guidance(self):
        context = week_context()
        cleaned, error = paid_writer.validate(valid_output(context), context)
        self.assertIsNone(error)
        self.assertEqual(len(cleaned["days"]), 7)
        self.assertIn("sınırını", cleaned["days"][0]["yorum"])

    def test_writer_receives_exact_focus_labels_and_anchors(self):
        context = week_context()
        prompt = json.loads(paid_writer._user_text(context, "en"))
        self.assertEqual(
            [day["focus"] for day in prompt["week"]["days"]],
            [paid_writer.FOCUS_TRANSLATIONS[day["focus"]] for day in context["days"]],
        )
        self.assertIn("Copy each given focus exactly", prompt["output_instruction"])
        self.assertIn("Never state a future outcome as certain", prompt["output_instruction"])
        self.assertEqual(prompt["week"]["days"][0]["focus_anchors"], list(paid_writer.ENGLISH_FOCUS_TERMS["relationships"]))
        self.assertNotIn("focus_anchors", context["days"][0])
        turkish_prompt = json.loads(paid_writer._user_text(context, "tr"))
        self.assertEqual(turkish_prompt["week"]["days"][0]["focus_anchors"], list(paid_writer.FOCUS_TERMS["ilişki"]))
        self.assertIn("32 ile 110", turkish_prompt["output_instruction"])
        self.assertIn("Geleceğe dair kesinlik", turkish_prompt["output_instruction"])

    def test_writer_rejects_unproven_domain_future_claim_and_technical_leak(self):
        context = week_context()
        output = valid_output(context)
        output["days"][0]["alanlar"] = ["work"]
        self.assertEqual(paid_writer.validate(output, context)[1], "alan_kanitla_uyusmuyor")
        output = valid_output(context)
        output["days"][1]["yorum"] = "İş yükün bugün yeni işin kesinleşecek, beklemeden kabul etmen gerektiğini gösteriyor. Bu gelişme kariyerinde kesin bir yön açacak ve bütün sorumluluklarını kolayca çözecek. Gün içindeki her talep sana daha iyi bir sonuç getirecek; bu nedenle mevcut işlerini düşünmeden bırakmalısın."
        self.assertEqual(paid_writer.validate(output, context)[1], "kesin_gelecek_iddiasi")
        output = valid_output(context)
        output["days"][2]["yorum"] = "Ev ve iç düzen bugün alan istiyor; transit bilgisi bu ritmin nedenini açıklıyor. Yakın çevrendeki hareket arttığında kendine sakin bir köşe açman, duygularını daha dengeli taşımanı sağlayabilir. Her çağrıya hemen dönme. Günü biraz yavaşlatmak, çevrendeki ritmi daha açık izlemeni ve kendi ihtiyacını fark etmeni kolaylaştırabilir."
        self.assertEqual(paid_writer.validate(output, context)[1], "teknik_terim_sizintisi")

    def test_deep_writer_accepts_only_evidence_bound_safe_paragraph(self):
        day = week_context()["days"][1]
        deep_prompt = json.loads(paid_writer._deep_user_text(day, "tr"))
        self.assertIn("\"yorum\"", deep_prompt["output_instruction"])
        text, error = paid_writer.validate_deep({"yorum": "İş yükünün içindeki ana öncelik bugün daha görünür hale gelebilir. Sorumlulukların arasından gerçekten sonuç getirecek işi seçtiğinde, günün temposunu daha sakin taşırsın. Her talebe aynı anda yetişmeye çalışmak yerine yapılabilir bir sıraya bağlı kal. Bu yaklaşım, hem emeğini korumana hem de gün sonunda zihnini daha açık tutmana yardım eder. Küçük bir işi tamamlamak, yeni bir sözü aceleyle vermekten daha değerli olabilir. Gün içinde bir konu tekrar önüne geldiğinde, ilk tepkiyle karar vermek yerine elindeki işi ve sınırını yeniden hatırla. Böylece emeğinin nereye aktığını daha bilinçli seçebilir, akşam saatlerinde kendine daha az dağınık bir alan bırakabilirsin."}, day)
        self.assertIsNone(error)
        self.assertIn("İş yükünün", text)

    def test_technical_guard_matches_whole_terms_not_ordinary_word_fragments(self):
        self.assertFalse(paid_writer._leaks_technical_terms("Kısa bir sunum için sakin hazırlık yap."))
        self.assertTrue(paid_writer._leaks_technical_terms("Sun bugün ilişkinizi yönetiyor."))
        self.assertTrue(paid_writer._leaks_technical_terms("Transit bilgisi sekizinci ev için konuşuyor."))

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
                paid_store.set_homepage_week_deep("user-a", "chart-a", "İş yükünün içindeki ana öncelik daha görünür hale gelebilir.", "2026-09-15", "deep-hash-a", "tr")
                self.assertEqual(paid_store.get_homepage_week("user-a", "chart-a", monday, "hash-a", "tr"), payload)
                self.assertEqual(paid_store.get_homepage_week_deep("user-a", "chart-a", "2026-09-15", "deep-hash-a", "tr"), "İş yükünün içindeki ana öncelik daha görünür hale gelebilir.")
                self.assertIsNone(paid_store.get_homepage_week("user-a", "chart-a", monday, "hash-a", "en"))
                self.assertIsNone(paid_store.get_homepage_week("user-b", "chart-a", monday, "hash-a", "tr"))
                self.assertIsNone(paid_store.get_homepage_week("user-a", "chart-a", monday, "hash-b", "tr"))
                self.assertGreaterEqual(paid_store.delete_user("user-a"), 1)
                self.assertIsNone(paid_store.get_homepage_week("user-a", "chart-a", monday, "hash-a", "tr"))
                self.assertIsNone(paid_store.get_homepage_week_deep("user-a", "chart-a", "2026-09-15", "deep-hash-a", "tr"))
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

    def test_deep_route_generates_once_then_reuses_day_cache(self):
        app = Flask(__name__)
        app.register_blueprint(paid_routes.paid_digest_bp)
        context = week_context()
        current_hour = datetime(2026, 9, 16, 15, 0, tzinfo=ZoneInfo("Europe/Istanbul"))
        chart = {"meta": {"engine_version": "test"}}
        deep_text = "İş yükünün içindeki asıl öncelik bugün daha belirginleşebilir. Sorumluluklarını aynı anda taşımaya çalıştığında zihnin dağılabilir; bu nedenle önce sonuç doğuracak işi seçmek sana daha sağlam bir yön verir. Gün içinde senden istenen her şeye hemen cevap vermek yerine, neyi gerçekten üstlenebileceğini sakin biçimde değerlendir. Böylece emeğini görünür sonuçlara ayırır, sınırını korur ve günün sonunda kendine daha açık bir alan bırakırsın. Küçük fakat tamamlanmış bir adım, hızlı görünmek için verilen yeni bir sözden daha kalıcı bir rahatlık sağlayabilir."
        with patch.object(paid_routes, "_load_owned_chart", return_value=((chart, "chart-1", "profile-1", "user-1"), None)), \
                patch.object(paid_routes, "current_hour_ist", return_value=current_hour), \
                patch.object(paid_routes, "_load_weekly_snapshots", return_value=([{"date": day["date"]} for day in context["days"]], 0)), \
                patch.object(paid_routes, "build_personal_week_context", return_value=context), \
                patch.object(paid_routes, "_sha256", return_value="evidence-hash"), \
                patch.object(paid_routes.paid_store, "get_homepage_week_deep", side_effect=[None, None, deep_text]), \
                patch.object(paid_routes.paid_store, "acquire_lock", return_value="owner"), \
                patch.object(paid_routes.paid_store, "release_lock"), \
                patch.object(paid_routes.paid_store, "set_homepage_week_deep"), \
                patch.object(paid_routes.paid_writer, "generate_deep", return_value=(deep_text, None)) as generate:
            first = app.test_client().post("/api/v2/pwa/digest/personal/deepen", json={"date": "2026-09-15"})
            second = app.test_client().post("/api/v2/pwa/digest/personal/deepen", json={"date": "2026-09-15"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.get_json()["kaynak"], "yeni_uretim")
        self.assertEqual(second.get_json()["kaynak"], "onbellek")
        self.assertEqual(first.get_json()["derin_yorum"], deep_text)
        generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
