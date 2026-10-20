"""Synthetic candidate review regressions: no real APK, signing, or Android."""
import copy
from io import BytesIO
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import review_rebuilt_candidate as candidate
from test_private_unsigned_apk import fake_elf


def row(member, sha="0" * 64, machine="EM_AARCH64"):
    return {
        "path": candidate.APK_NAME + "!" + member,
        "sha256": sha, "machine": machine,
        "load_4k": True, "load_16k": True,
        "missing_needed_api24": [], "strong_unresolved_api24": [],
        "version_provider_mismatches_api24": [],
    }


def fixtures():
    native = [row("lib/arm64-v8a/libdummy" + str(i) + ".so") for i in range(91)]
    native.append(row(candidate.JNI_PATH, candidate.JNI_SHA256))
    for lib, sha in candidate.PINNED_ELF.items():
        native.append(row(candidate.NESTED[0] + "!chaquopy/lib/" + lib, sha))
    native.append(row(candidate.NESTED[1] + "!debugpy.so", machine="EM_X86_64"))
    return {
        "unsigned-apk-receipt.json": {
            "source_head": candidate.SOURCE_HEAD, "apk_name": candidate.APK_NAME,
            "sha256": candidate.APK_SHA256, "bytes": candidate.APK_BYTES,
            "historical_unsigned_sha256": candidate.HISTORICAL_SHA256,
            "matches_historical_unsigned": False, "signed": False,
            "installed": False, "android_executed": False, "crc_valid": True,
            "zipalign_16k_pass": True, "internet_absent": True,
            "packaged_rebuilt_elf": candidate.PINNED_ELF.copy(),
        },
        "historical-comparison.json": {
            "historical_unsigned_apk_sha256": candidate.HISTORICAL_SHA256,
            "candidate_apk_sha256": candidate.APK_SHA256,
            "historical_apk_available": False,
            "matches_historical_apk_sha256": False,
            "elf_inventory_matches": True, "unchanged_elf": 96,
            "elf_differences": [{
                "member": candidate.JNI_PATH,
                "candidate_sha256": candidate.JNI_SHA256,
            }],
            "historical_contract_modified": False,
            "dependency_graph_comparison": {
                name: {"same_components": True, "added": [], "removed": []}
                for name in ("diagnosticDebugCompileClasspath",
                             "diagnosticDebugRuntimeClasspath",
                             "diagnosticStagingCompileClasspath",
                             "diagnosticStagingRuntimeClasspath")
            },
        },
        "apk-native-audit.json": {
            "apk_sha256": candidate.APK_SHA256,
            "summary": {
                "elf_total": 97, "android_arm64": 96, "arm64_4k_pass": 96,
                "arm64_16k_pass": 96, "other_machine": 1,
                "missing_needed": 0, "strong_unresolved": 0, "version_mismatch": 0,
            }, "libraries": native,
        },
        "build-result.json": {
            "code_head": candidate.SOURCE_HEAD, "exit_code": 0,
            "native_target": "arm64-v8a", "unsigned_overlay": True,
            "command": [":TMessagesProj:assembleDiagnosticDebug"],
        },
        "private-preservation.json": {
            "apk_sha256": candidate.APK_SHA256,
            "contains_unsigned_apk": True, "contains_private_key": False,
            "recovered_copy_verified": True, "archive_crc_valid": True,
            "verified_members": 58, "members": 58, "sha256": "f" * 64,
        },
        "apk-diagnostic-check.json": {
            "apk_sha256": candidate.APK_SHA256, "bytes": candidate.APK_BYTES,
            "zip_crc": "passed", "distribution_allowed": False,
            "manifest": {
                "validation": "passed",
                "package": "io.github.jose22yt.flexygram.diagnostic",
                "permissions": ["android.permission.ACCESS_NETWORK_STATE"],
            },
            "compiled_isolation": {"api_id_zero": True, "api_hash_empty": True},
            "variant_policy": {"all_capabilities_disabled": True},
            "all_translation_gates_passed": True,
        },
        "native-linked-guards.json": {
            "guards": [{"instructions": ["ret"], "body_absent": True}
                       for _ in range(3)],
            "packaged_text_matches_linked": True, "runtime_execution": False,
        },
        "apk-native-acceptance.json": {
            "status": "STATIC_CLEAN_PENDING_ANDROID",
            "arm64_elf": 96, "non_target_payloads": 1, "blockers": [],
            "runtime_required": True, "distribution_allowed": False,
        },
        "source-input-receipt.json": {
            "head": candidate.SOURCE_HEAD, "signing_authorized": False,
            "installation_authorized": False, "experiment_overlay_only": True,
        },
        "overlay.json": {
            "source_head": candidate.SOURCE_HEAD, "unsigned_diagnostic": True,
            "production_and_policy_unchanged": True,
        },
        "android-code-continuity.json": {
            "source_head": candidate.SOURCE_HEAD,
            "android_gradle_jni_module_diff_empty": True,
        },
        "lab-probe.json": {
            "android_executed": False, "apk_installed": False,
            "offline_boot_validated": False,
        },
        "graph-result.json": {
            "code_head": candidate.SOURCE_HEAD, "exit_code": 0,
        },
        "native-231.json": {
            "status": "PASS", "tests_run": 231, "passed": 231,
            "minimum_required": 231, "failures": 0, "errors": 0,
            "skipped": 0, "expected_failures": 0, "unexpected_successes": 0,
            "discovery_incomplete": False,
        },
        "native-231-opt.json": {
            "status": "PASS", "tests_run": 231, "passed": 231,
            "minimum_required": 231, "failures": 0, "errors": 0,
            "skipped": 0, "expected_failures": 0, "unexpected_successes": 0,
            "discovery_incomplete": False,
        },
    }


class CandidateReviewTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.records = fixtures()

    def test_valid_synthetic_metadata_is_not_a_runtime_pass(self):
        result = candidate.review_records(self.records)
        self.assertEqual(len(result), 97)
        with patch.object(candidate, "check_index", return_value=self.records):
            report = candidate.review(self.root)
        self.assertEqual(report["status"], "CANDIDATE_METADATA_REVIEWED_BYTES_NOT_VERIFIED")
        self.assertFalse(report["physical_apk_checked"])
        self.assertFalse(report["android_runtime_validated"])

    def test_changed_candidate_digest_is_rejected(self):
        self.records["unsigned-apk-receipt.json"]["sha256"] = "a" * 64
        with self.assertRaises(ValueError):
            candidate.review_records(self.records)

    def test_signed_or_installed_candidate_is_rejected(self):
        for key in ("signed", "installed", "android_executed"):
            records = fixtures()
            records["unsigned-apk-receipt.json"][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                candidate.review_records(records)

    def test_legacy_contract_mutation_is_rejected(self):
        self.records["historical-comparison.json"]["historical_contract_modified"] = True
        with self.assertRaises(ValueError):
            candidate.review_records(self.records)

    def test_native_elf_mismatch_rejected_even_if_summary_passes(self):
        self.records["apk-native-audit.json"]["libraries"][-2]["sha256"] = "c" * 64
        with self.assertRaises(ValueError):
            candidate.review_records(self.records)

    def test_changed_jni_not_hidden_as_unchanged(self):
        self.records["historical-comparison.json"]["elf_differences"] = []
        with self.assertRaises(ValueError):
            candidate.review_records(self.records)

    def test_unsafe_audit_path_rejected(self):
        self.records["apk-native-audit.json"]["libraries"][0]["path"] = (
            candidate.APK_NAME + "!lib/../libhack.so")
        with self.assertRaises(ValueError):
            candidate.review_records(self.records)

    def test_missing_guard_rejected(self):
        self.records["native-linked-guards.json"]["guards"].pop()
        with self.assertRaises(ValueError):
            candidate.review_records(self.records)

    def test_partial_gate_rejected(self):
        self.records["native-231-opt.json"]["tests_run"] = 230
        with self.assertRaises(ValueError):
            candidate.review_records(self.records)

    def test_runtime_claim_in_lab_report_rejected(self):
        self.records["lab-probe.json"]["android_executed"] = True
        with self.assertRaises(ValueError):
            candidate.review_records(self.records)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            candidate.strict_json(b'{"sha":"a","sha":"b"}')

    def test_nonfinite_json_rejected(self):
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            candidate.strict_json(b'{"duration":NaN}')

    def test_index_rejects_unpinned_or_missing_evidence(self):
        (self.root / "evidence-sha256.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "index pin"):
            candidate.check_index(self.root)

    def test_index_rejects_symlink(self):
        (self.root / "evidence-sha256.json").symlink_to(self.root / "missing")
        with self.assertRaises(ValueError):
            candidate.check_index(self.root)

    def test_missing_physical_apk_remains_blocked(self):
        with patch.object(candidate, "check_index", return_value=self.records):
            self.assertEqual(candidate.main(["--apk", str(self.root / candidate.APK_NAME)]), 1)

    def test_wrong_physical_apk_bytes_rejected(self):
        apk = self.root / candidate.APK_NAME
        apk.write_bytes(b"not the approved bytes")
        with self.assertRaisesRegex(ValueError, "size/name/SHA256"):
            candidate.inspect_private_apk(apk, {})

    def test_unsigned_apk_signature_member_rejected_after_pin_check(self):
        apk = self.root / candidate.APK_NAME
        with zipfile.ZipFile(apk, "w") as z:
            z.writestr("AndroidManifest.xml", "fixture")
            z.writestr("META-INF/SIGNER.RSA", b"fake")
        with patch.object(candidate, "APK_SHA256", candidate.file_sha(apk)):
            with patch.object(candidate, "APK_BYTES", apk.stat().st_size):
                with self.assertRaisesRegex(ValueError, "JAR-signed"):
                    candidate.inspect_private_apk(apk, {})

    def test_physical_duplicate_member_rejected(self):
        apk = self.root / candidate.APK_NAME
        with zipfile.ZipFile(apk, "w") as z:
            z.writestr("AndroidManifest.xml", "fixture")
            z.writestr("AndroidManifest.xml", "fixture2")
        with patch.object(candidate, "APK_SHA256", candidate.file_sha(apk)):
            with patch.object(candidate, "APK_BYTES", apk.stat().st_size):
                with self.assertRaisesRegex(ValueError, "duplicates"):
                    candidate.inspect_private_apk(apk, {})


    def synthetic_physical_apk(self, change=None, omit=None, nested_duplicate=False):
        """Create an isolated 97-ELF test APK with no Android app or identity."""
        apk = self.root / candidate.APK_NAME
        expected = {}
        with zipfile.ZipFile(apk, "w") as outer:
            outer.writestr("AndroidManifest.xml", b"synthetic manifest, not installable")
            for i in range(30):
                name = "lib/arm64-v8a/libsynthetic" + str(i) + ".so"
                if name == omit:
                    continue
                data = fake_elf(alignment=4096 if name == change else 16384)
                outer.writestr(name, data)
                expected[name] = (hashlib.sha256(data).hexdigest(), "EM_AARCH64")
            for n, count in zip(candidate.NESTED, (19, 48)):
                memory = BytesIO()
                with zipfile.ZipFile(memory, "w") as inner:
                    for i in range(count):
                        name = "lib/test" + str(i) + ".so"
                        machine = "EM_X86_64" if n == candidate.NESTED[1] and i == 47 else "EM_AARCH64"
                        data = fake_elf(arch=62 if machine == "EM_X86_64" else 183)
                        inner.writestr(name, data)
                        expected[n + "!" + name] = (hashlib.sha256(data).hexdigest(), machine)
                    if nested_duplicate and n == candidate.NESTED[0]:
                        inner.writestr("lib/test0.so", fake_elf())
                outer.writestr(n, memory.getvalue())
        return apk, expected

    def physically_checked(self, apk, expected):
        with patch.object(candidate, "APK_SHA256", candidate.file_sha(apk)):
            with patch.object(candidate, "APK_BYTES", apk.stat().st_size):
                return candidate.inspect_private_apk(apk, expected)

    def test_synthetic_97_elf_physical_apk_passes_static_only(self):
        apk, expected = self.synthetic_physical_apk()
        result = self.physically_checked(apk, expected)
        self.assertEqual(result["elf_total"], 97)
        self.assertEqual(result["arm64"], 96)
        self.assertFalse(result["android_runtime_validated"])

    def test_physical_elf_digest_mismatch_is_blocked(self):
        apk, expected = self.synthetic_physical_apk()
        expected["lib/arm64-v8a/libsynthetic0.so"] = ("f" * 64, "EM_AARCH64")
        with self.assertRaisesRegex(ValueError, "Physical ELF digest"):
            self.physically_checked(apk, expected)

    def test_physical_4k_only_elf_is_blocked(self):
        apk, expected = self.synthetic_physical_apk(
            change="lib/arm64-v8a/libsynthetic0.so")
        with self.assertRaisesRegex(ValueError, "16 KB PT_LOAD"):
            self.physically_checked(apk, expected)

    def test_physical_missing_elf_is_blocked(self):
        apk, expected = self.synthetic_physical_apk()
        expected["lib/arm64-v8a/never-packaged.so"] = ("0" * 64, "EM_AARCH64")
        with self.assertRaisesRegex(ValueError, "ELF inventory mismatch"):
            self.physically_checked(apk, expected)

    def test_physical_nested_duplicate_is_blocked(self):
        apk, expected = self.synthetic_physical_apk(nested_duplicate=True)
        with self.assertRaisesRegex(ValueError, "Nested ZIP duplicates"):
            self.physically_checked(apk, expected)

    def test_physical_symlink_entry_is_blocked(self):
        apk, expected = self.synthetic_physical_apk()
        with zipfile.ZipFile(apk, "a") as outer:
            link = zipfile.ZipInfo("assets/unsafe-link")
            link.create_system = 3
            link.external_attr = (0o120777 << 16)
            outer.writestr(link, "outside")
        with self.assertRaisesRegex(ValueError, "Unsafe APK ZIP member type"):
            self.physically_checked(apk, expected)


    def indexed_synthetic_evidence(self):
        names = sorted(candidate.NEEDED)
        names += ["fixture%02d.txt" % i for i in range(44 - len(names))]
        index = {}
        for name in names:
            data = b"{}" if name.endswith(".json") else b"synthetic log"
            (self.root / name).write_bytes(data)
            index[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        raw = (json.dumps(index, sort_keys=True, indent=2) + "\n").encode()
        (self.root / "evidence-sha256.json").write_bytes(raw)
        pin = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        return names, pin

    def test_synthetic_evidence_chain_44_files_valid(self):
        names, pin = self.indexed_synthetic_evidence()
        with patch.object(candidate, "INDEX_BLOB_SHA", pin):
            records = candidate.check_index(self.root)
        self.assertEqual(len(names), 44)
        self.assertIn("build-result.json", records)
        self.assertEqual(records["build-result.json"], {})

    def test_mutated_evidence_file_rejected_against_index(self):
        names, pin = self.indexed_synthetic_evidence()
        (self.root / "build-result.json").write_bytes(b'{"modified":true}')
        with patch.object(candidate, "INDEX_BLOB_SHA", pin):
            with self.assertRaisesRegex(ValueError, "Candidate evidence changed"):
                candidate.check_index(self.root)

    def test_index_rejects_symlinked_child(self):
        names, pin = self.indexed_synthetic_evidence()
        child = self.root / "build-result.json"
        real = self.root / "original"
        child.rename(real)
        child.symlink_to(real)
        with patch.object(candidate, "INDEX_BLOB_SHA", pin):
            with self.assertRaisesRegex(ValueError, "Missing or unsafe"):
                candidate.check_index(self.root)


if __name__ == "__main__":
    unittest.main()
