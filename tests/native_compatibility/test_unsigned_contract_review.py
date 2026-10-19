"""Unsigned APK review is a host-only evidence gate, never signing approval."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "tools/native_compatibility/review_unsigned_contract.py"
spec = importlib.util.spec_from_file_location("p04c_unsigned_contract_review", SCRIPT)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class UnsignedContractReviewTests(unittest.TestCase):
    def test_current_published_evidence_yields_blocked_candidate_only(self):
        candidate = review.verify()
        self.assertEqual(candidate["status"], "UNSIGNED_EVIDENCE_REVIEWED_SIGNING_BLOCKED")
        self.assertEqual(candidate["unsigned_apk_sha256"], review.APK_SHA256)
        self.assertEqual(candidate["reviewed_arm64_elf"], 96)
        self.assertEqual(candidate["evidence_files_verified"], 44)
        self.assertTrue(candidate["historical_lab_contract_preserved"])
        for field in ("certificate_sha256", "signed_apk_sha256", "signed_runner_sha256"):
            self.assertIsNone(candidate[field])
        self.assertFalse(candidate["signing_authorized"])
        self.assertFalse(candidate["android_runtime_validated"])
        self.assertFalse(candidate["distribution_allowed"])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "published-evidence"

    def prepare_copy(self):
        shutil.copytree(review.EVIDENCE, self.folder)

    def mutate(self, filename, edit):
        path = self.folder / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        edit(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_any_changed_evidence_digest_is_rejected(self):
        self.prepare_copy()
        self.mutate("apk-native-acceptance.json", lambda d: d.update({"arm64_elf": 95}))
        with self.assertRaisesRegex(ValueError, "Evidence digest mismatch"):
            review.verify(self.folder)

    def test_missing_evidence_is_rejected(self):
        self.prepare_copy()
        (self.folder / "native-linked-guards.json").unlink()
        with self.assertRaisesRegex(ValueError, "Evidence file missing"):
            review.verify(self.folder)

    def test_symlinked_evidence_file_is_rejected(self):
        self.prepare_copy()
        victim = self.folder / "apk-native-acceptance.json"
        actual = Path(self.temp.name) / "outside.json"
        victim.rename(actual)
        victim.symlink_to(actual)
        with self.assertRaisesRegex(ValueError, "Evidence file missing/unsafe"):
            review.verify(self.folder)

    def test_forged_signing_status_rejected_even_with_updated_inventory(self):
        self.prepare_copy()
        self.mutate("unsigned-apk-receipt.json", lambda d: d.update({"signature": "signed"}))
        with patch.object(review, "check_evidence_files", return_value=44):
            with self.assertRaisesRegex(ValueError, "Unsigned APK receipt"):
                review.verify(self.folder)

    def test_forged_runtime_success_rejected_even_with_updated_inventory(self):
        self.prepare_copy()
        self.mutate("unsigned-apk-receipt.json", lambda d: d.update({"android_runtime_validated": True}))
        with patch.object(review, "check_evidence_files", return_value=44):
            with self.assertRaisesRegex(ValueError, "Unsigned APK receipt"):
                review.verify(self.folder)

    def test_per_library_alignment_failure_is_not_hidden_by_summary(self):
        self.prepare_copy()
        def corrupt(d):
            row = next(x for x in d["libraries"] if x["machine"] == "EM_AARCH64")
            row["load_16k"] = False
        self.mutate("apk-native-audit.json", corrupt)
        with patch.object(review, "check_evidence_files", return_value=44):
            with self.assertRaisesRegex(ValueError, "Per-library"):
                review.verify(self.folder)

    def test_rebuilt_wheel_digest_change_is_rejected(self):
        self.prepare_copy()
        def corrupt(d):
            row = next(x for x in d["wheels"] if x["rebuilt"])
            row["sha256"] = "0" * 64
        self.mutate("experimental-wheels-manifest.json", corrupt)
        with patch.object(review, "check_evidence_files", return_value=44):
            with self.assertRaisesRegex(ValueError, "Rebuilt wheel inventory"):
                review.verify(self.folder)

    def test_network_permission_reintroduced_is_rejected(self):
        self.prepare_copy()
        self.mutate("apk-diagnostic-check.json",
                    lambda d: d["manifest"]["permissions"].append("android.permission.INTERNET"))
        with patch.object(review, "check_evidence_files", return_value=44):
            with self.assertRaisesRegex(ValueError, "Diagnostic APK safety"):
                review.verify(self.folder)

    def test_modified_jni_guard_is_rejected(self):
        self.prepare_copy()
        self.mutate("native-linked-guards.json",
                    lambda d: d["guards"][0].update({"instructions": ["ret", "nop"]}))
        with patch.object(review, "check_evidence_files", return_value=44):
            with self.assertRaisesRegex(ValueError, "JNI guards"):
                review.verify(self.folder)

    def test_cli_cannot_claim_pass_for_missing_evidence(self):
        self.assertEqual(review.main(["--evidence", str(self.folder)]), 1)


if __name__ == "__main__":
    unittest.main()
