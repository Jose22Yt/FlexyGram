"""Synthetic private APK byte checks, never Android execution or signing."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import verify_private_unsigned_apk as inspect_apk


def fake_elf(arch=183, alignment=16384):
    data = bytearray(160)
    data[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<H", data, 18, arch)
    struct.pack_into("<Q", data, 32, 64)
    struct.pack_into("<HH", data, 54, 56, 1)
    struct.pack_into("<IIQQQQQQ", data, 64, 1, 5, 0, 0, 0,
                     len(data), len(data), alignment)
    return bytes(data)


class PrivateUnsignedAPKTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.evidence = self.root / "evidence"
        self.evidence.mkdir()
        self.apk = self.root / "synthetic-unsigned.apk"
        self.contents = {}
        self.arch = {}
        for i in range(97):
            if i < 30:
                name = "lib/arm64-v8a/libfixture" + str(i) + ".so"
            elif i < 49:
                name = inspect_apk.NESTED[0] + "!lib/fixture" + str(i) + ".so"
            else:
                name = inspect_apk.NESTED[1] + "!lib/fixture" + str(i) + ".so"
            self.contents[name] = fake_elf(62 if i == 96 else 183)
            self.arch[name] = "EM_X86_64" if i == 96 else "EM_AARCH64"

    def materialize(self, extra=None, duplicate=None):
        with zipfile.ZipFile(self.apk, "w") as apk:
            for name, data in self.contents.items():
                if "!" not in name:
                    apk.writestr(name, data)
            for nested_name in inspect_apk.NESTED:
                nested_bytes = BytesIO()
                with zipfile.ZipFile(nested_bytes, "w") as nested:
                    for name, data in self.contents.items():
                        if name.startswith(nested_name + "!"):
                            nested.writestr(name.split("!", 1)[1], data)
                apk.writestr(nested_name, nested_bytes.getvalue())
            for name, value in (extra or {}).items():
                apk.writestr(name, value)
            if duplicate:
                apk.writestr(duplicate, self.contents[duplicate])
        audit = {
            "libraries": [
                {"path": self.apk.name + "!" + name,
                 "machine": self.arch[name],
                 "sha256": hashlib.sha256(data).hexdigest()}
                for name, data in self.contents.items()
            ]
        }
        (self.evidence / "apk-native-audit.json").write_text(json.dumps(audit))
        (self.evidence / "unsigned-apk-receipt.json").write_text(json.dumps(
            {"apk_filename": self.apk.name}))
        self.private_sha = hashlib.sha256(self.apk.read_bytes()).hexdigest()

    def check(self):
        with patch.object(inspect_apk.review, "verify", return_value={}):
            with patch.object(inspect_apk.review, "APK_BYTES", self.apk.stat().st_size):
                with patch.object(inspect_apk.review, "APK_SHA256", self.private_sha):
                    return inspect_apk.verify(self.apk, self.evidence)

    def test_complete_synthetic_apk_inventory_passes_unsigned_only(self):
        self.materialize()
        outcome = self.check()
        self.assertEqual(outcome["native_entries"], 97)
        self.assertEqual(outcome["arm64_elf"], 96)
        self.assertFalse(outcome["signed"])
        self.assertFalse(outcome["android_runtime_validated"])

    def test_native_elf_mismatch_is_rejected(self):
        self.materialize()
        self.contents["lib/arm64-v8a/libfixture0.so"] = fake_elf(183, 4096)
        self.materialize()
        # Corrupt published audit to retain old expected digest.
        audit = self.evidence / "apk-native-audit.json"
        contents = json.loads(audit.read_text())
        contents["libraries"][0]["sha256"] = "0" * 64
        audit.write_text(json.dumps(contents))
        with self.assertRaisesRegex(ValueError, "ELF SHA256 mismatch"):
            self.check()

    def test_4096_aligned_elf_not_admitted_as_16k(self):
        first = "lib/arm64-v8a/libfixture0.so"
        self.contents[first] = fake_elf(183, 4096)
        self.materialize()
        with self.assertRaisesRegex(ValueError, "16 KB PT_LOAD"):
            self.check()

    def test_wrong_architecture_cannot_pass_matching_digest(self):
        first = "lib/arm64-v8a/libfixture0.so"
        self.contents[first] = fake_elf(62)
        self.materialize()
        with self.assertRaisesRegex(ValueError, "architecture mismatch"):
            self.check()

    def test_unreviewed_elf_cannot_be_added(self):
        self.materialize(extra={"lib/arm64-v8a/libextra.so": fake_elf()})
        with self.assertRaisesRegex(ValueError, "inventory differs"):
            self.check()

    def test_duplicate_zip_member_rejected(self):
        self.materialize(duplicate="lib/arm64-v8a/libfixture0.so")
        with self.assertRaisesRegex(ValueError, "APK ZIP duplicate"):
            self.check()

    def test_apk_v1_jar_signature_rejected(self):
        self.materialize(extra={"META-INF/SIGNER.RSA": b"fake"})
        with self.assertRaisesRegex(ValueError, "Unexpected JAR signature"):
            self.check()

    def test_apk_digest_mismatch_rejected_before_parsing(self):
        self.materialize()
        with patch.object(inspect_apk.review, "verify", return_value={}):
            with patch.object(inspect_apk.review, "APK_BYTES", self.apk.stat().st_size):
                with self.assertRaisesRegex(ValueError, "Private APK SHA256"):
                    inspect_apk.verify(self.apk, self.evidence)

    def test_no_real_apk_available_is_blocked(self):
        self.assertEqual(inspect_apk.main([
            "--apk", str(self.apk), "--evidence", str(self.evidence)]), 1)


if __name__ == "__main__":
    unittest.main()
