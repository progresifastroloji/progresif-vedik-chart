import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from turkish_narrative import (MARKER, DIMENSIONS, EditorialError, generate_checked, marked, parse_review, review_request)
from vertex_bridge_client import call_vertex_bridge, VertexBridgeClientError

def payload(text):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}], "usageMetadata": {"totalTokenCount": 10}}

def report(ok=True):
    return payload(json.dumps({"scores": {k: 4 if ok else 2 for k in DIMENSIONS}, "reasons": {k: "Görev paylaşımı kaynağa uygun anlatıldı." for k in DIMENSIONS}, "unsupported_claims": [], "issues": [] if ok else ["Önerinin konusu belirsiz."]}))

class TurkishNarrativeTest(unittest.TestCase):
    def setUp(self):
        self.request = {"systemInstruction": {"parts": [{"text": MARKER}]}, "contents": [{"role": "user", "parts": [{"text": "Doğrulanmış konu: görev paylaşımı."}]}]}

    def test_marker_only_in_system(self):
        self.assertTrue(marked(self.request))
        self.assertFalse(marked({"contents": [{"parts": [{"text": MARKER}]}]}))

    def test_pass_preserves_draft_and_aggregates_usage(self):
        original = copy.deepcopy(self.request)
        outputs = iter([payload("Görev paylaşımını konuşabilirsiniz."), report()])
        calls = []
        def call(identifier, request):
            calls.append(request)
            return identifier, next(outputs)
        identifier, value = generate_checked("test", self.request, call)
        self.assertEqual(identifier, "test")
        self.assertEqual(value["usageMetadata"]["totalTokenCount"], 20)
        self.assertFalse(value["editorialQuality"]["repaired"])
        self.assertEqual(original, self.request)
        self.assertEqual(len(calls), 2)
        self.assertFalse(marked(calls[1]))

    def test_repair_is_bounded_and_carries_feedback(self):
        outputs = iter([payload("Genel öneri."), report(False), payload("Görevleri kimin üstleneceğini konuşabilirsiniz."), report()])
        calls = []
        def call(identifier, request):
            calls.append(request)
            return identifier, next(outputs)
        _, value = generate_checked("test", self.request, call)
        self.assertTrue(value["editorialQuality"]["repaired"])
        self.assertIn("Önerinin konusu belirsiz", calls[2]["contents"][-1]["parts"][0]["text"])
        self.assertEqual(len(calls), 4)

    def test_second_failure_never_publishes(self):
        outputs = iter([payload("x"), report(False), payload("x"), report(False)])
        with self.assertRaises(EditorialError):
            generate_checked("test", self.request, lambda i, r: (i, next(outputs)))

    def test_malformed_review_fails_closed(self):
        for text in ('{}', '{"scores":null}', 'not json'):
            with self.subTest(text=text), self.assertRaises(EditorialError):
                parse_review(payload(text))

    def test_truncated_review_is_not_accepted_even_with_valid_json(self):
        value = report()
        value["candidates"][0]["finishReason"] = "MAX_TOKENS"
        with self.assertRaises(EditorialError):
            parse_review(value)
        self.assertEqual(review_request(self.request, payload("x"))["generationConfig"]["maxOutputTokens"], 6000)

    def test_editor_uses_validated_analysis_not_full_archive(self):
        self.request["contents"][0]["parts"][0]["text"] = "DOĞRULANMIŞ AŞAMA 1: görev paylaşımı\n\nTAM KAYNAK SIRASI: fazla arşiv"
        request = review_request(self.request, payload("Görev paylaşımı"))
        text = request["contents"][0]["parts"][0]["text"]
        self.assertIn("DOĞRULANMIŞ", text)
        self.assertNotIn("fazla arşiv", text)

    def test_editor_distinguishes_general_traditional_theme_from_personal_claim(self):
        request = review_request(self.request, payload("Satürn döneminin geleneksel genel teması."))
        instruction = request["systemInstruction"]["parts"][0]["text"]
        self.assertIn("geleneksel genel temasını açıklamak desteksiz iddia değildir", instruction)
        self.assertIn("yalnız puanı 3 veya altına indiren", instruction)
        self.assertEqual(request["generationConfig"]["thinkingConfig"]["thinkingLevel"], "MEDIUM")

    @patch("vertex_bridge_client._call_vertex_bridge_raw")
    def test_unmarked_paths_have_one_call(self, call):
        call.return_value = ("en", payload("English"))
        call_vertex_bridge("en", {"contents": [{"parts": [{"text": "English"}]}]})
        self.assertEqual(call.call_count, 1)

    @patch("vertex_bridge_client._call_vertex_bridge_raw")
    def test_invalid_editor_returns_safe_nonretryable_error(self, call):
        call.side_effect = [("a", payload("x")), ("b", payload("{}"))]
        with self.assertRaises(VertexBridgeClientError) as raised:
            call_vertex_bridge("tr-test", self.request)
        self.assertEqual(raised.exception.code, "vertex_narrative_quality_failed")
        self.assertFalse(raised.exception.retryable)

    def test_corpus_split_no_duplicate_questions(self):
        cases = json.loads((Path(__file__).parent / "fixtures/turkish_narrative_cases.json").read_text())
        self.assertEqual(len(cases), 40)
        self.assertEqual(sum(x["split"] == "holdout" for x in cases), 20)
        self.assertEqual(len({x["question"] for x in cases}), 40)
        self.assertTrue(all("reference" not in x for x in cases if x["split"] == "holdout"))

    @patch("vertex_bridge_client._call_vertex_bridge_raw")
    def test_editorial_provider_error_does_not_restart_chain(self, call):
        call.side_effect = VertexBridgeClientError("vertex_bridge_unreachable", 504, retryable=True)
        with self.assertRaises(VertexBridgeClientError) as raised:
            call_vertex_bridge("tr-test", self.request)
        self.assertEqual(raised.exception.code, "vertex_narrative_provider_failed")
        self.assertFalse(raised.exception.retryable)
        self.assertIsNotNone(call.call_args.kwargs["deadline"])
        self.assertEqual(call.call_count, 1)
