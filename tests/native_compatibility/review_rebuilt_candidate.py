#!/usr/bin/env python3
"""Fail-closed P0.4c rebuilt unsigned *candidate* review (NOT an Android contract).

Metadata review checks the committed receipt chain against a pinned Git blob and
explicit candidate values. --apk additionally checks the actual private bytes.
Never changes the historical unsigned/v1 pins, signs, installs or enables services.
"""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import stat
import struct
import zipfile

from verify_private_unsigned_apk import elf_alignment, NESTED

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/security-p04c/evidence-unsigned-rebuild-20261020"
INDEX_BLOB_SHA = "d668ab49458669e0ca5fc63102d8b19653e373e8"
INDEX_SHA256 = "fff31dd27ffc69b1aed2da19428bf0e5d0eabdf51c06d2ca4828db95b74a05b7"
SOURCE_HEAD = "1177ceb8f4351b1626dd65e3dbd657f3b0ff159f"
APK_NAME = "flexygram-v13.0.2(1261)-diagnostic-debug-unsigned.apk"
APK_SHA256 = "291881863ea81418fa6cb12104b6eaea4aee2403822894da2143a51f3030bdd5"
APK_BYTES = 113080183
HISTORICAL_SHA256 = "ddb7b017838a2a13991ac09154bbf252a11d62326e9a588349ca03c115e01699"
JNI_PATH = "lib/arm64-v8a/libtmessages.49.so"
JNI_SHA256 = "756e53d23f29ecca32d7c9706375494cdf2217d0db8d314a4195d0174400912b"
PINNED_ELF = {
    "libexslt.so": "f8e9e0fc0fa7507f3391bacb5c08a16dc9fdab73ca23de48f8adb2dfcca7a194",
    "libfreetype.so": "d086a897a1c1cfa517b9e46c28d762f817af41bde96b2eda3bf6e6b12220eb01",
    "libxml2.so": "e282a655ebbe07443cd743bb9dd00a152bfed7edb091d862f0a4e74afc1eff04",
    "libxslt.so": "827d113f3045205b205b52d0e4fe2e59998bd3b471368314415a2c3e91571660",
}
NEEDED = frozenset((
    "unsigned-apk-receipt.json", "historical-comparison.json", "apk-native-audit.json",
    "apk-native-acceptance.json", "apk-diagnostic-check.json", "native-linked-guards.json",
    "native-231.json", "native-231-opt.json", "build-result.json",
    "private-preservation.json", "android-code-continuity.json", "lab-probe.json",
    "source-input-receipt.json", "overlay.json", "graph-result.json",
    "apksigner-unsigned.log",
))
HEX = re.compile(r"[0-9a-f]{64}\Z")
FILENAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*\Z")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def regular_file(path: Path):
    require(path.is_file() and not path.is_symlink() and
            not any(p.is_symlink() for p in path.parents), "Missing or unsafe file")


def file_sha(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_json(data: bytes):
    def unique(pairs):
        out = {}
        for name, value in pairs:
            require(name not in out, "Duplicate JSON key")
            out[name] = value
        return out

    def reject_constant(_value):
        raise ValueError("Non-finite JSON number")

    return json.loads(data, object_pairs_hook=unique, parse_constant=reject_constant)


def read_json(path):
    regular_file(path)
    return strict_json(path.read_bytes())


def check_index(folder: Path):
    require(folder.is_dir() and not folder.is_symlink() and
            not any(p.is_symlink() for p in folder.parents), "Unsafe evidence directory")
    index = folder / "evidence-sha256.json"
    regular_file(index)
    contents = index.read_bytes()
    git_blob = hashlib.sha1(b"blob " + str(len(contents)).encode("ascii") +
                            b"\0" + contents).hexdigest()
    require(git_blob == INDEX_BLOB_SHA and
            hashlib.sha256(contents).hexdigest() == INDEX_SHA256,
            "Candidate evidence index pin mismatch")
    inventory = strict_json(contents)
    require(isinstance(inventory, dict) and len(inventory) == 44 and
            NEEDED <= inventory.keys(), "Incomplete candidate evidence inventory")
    for name, entry in inventory.items():
        require(type(name) is str and FILENAME.fullmatch(name) and name not in (".", ".."),
                "Unsafe candidate evidence filename")
        require(isinstance(entry, dict) and type(entry.get("bytes")) is int and
                entry["bytes"] >= 0 and isinstance(entry.get("sha256"), str) and
                HEX.fullmatch(entry["sha256"]), "Invalid evidence index entry")
        file = folder / name
        regular_file(file)
        require(file.stat().st_size == entry["bytes"] and
                file_sha(file) == entry["sha256"], "Candidate evidence changed: " + name)
    return {name: read_json(folder / name) for name in NEEDED if name.endswith(".json")}


def review_records(r):
    receipt, audit = r["unsigned-apk-receipt.json"], r["apk-native-audit.json"]
    compare = r["historical-comparison.json"]
    compiled = r["build-result.json"]
    preserve = r["private-preservation.json"]
    diagnostic = r["apk-diagnostic-check.json"]
    guards = r["native-linked-guards.json"]
    acceptance = r["apk-native-acceptance.json"]
    source = r["source-input-receipt.json"]
    overlay = r["overlay.json"]
    history = r["android-code-continuity.json"]
    lab = r["lab-probe.json"]
    graph = r["graph-result.json"]
    require(receipt["source_head"] == SOURCE_HEAD and
            receipt["apk_name"] == APK_NAME and
            receipt["sha256"] == APK_SHA256 and receipt["bytes"] == APK_BYTES and
            receipt["historical_unsigned_sha256"] == HISTORICAL_SHA256 and
            receipt["matches_historical_unsigned"] is False and
            receipt["signed"] is False and receipt["installed"] is False and
            receipt["android_executed"] is False and
            receipt["crc_valid"] is True and receipt["zipalign_16k_pass"] is True and
            receipt["internet_absent"] is True, "Unsigned candidate receipt mismatch")
    require(compiled["code_head"] == SOURCE_HEAD and compiled["exit_code"] == 0 and
            compiled["native_target"] == "arm64-v8a" and
            compiled["unsigned_overlay"] is True and
            ":TMessagesProj:assembleDiagnosticDebug" in compiled["command"],
            "Candidate build result mismatch")
    require(source["head"] == SOURCE_HEAD and source["signing_authorized"] is False and
            source["installation_authorized"] is False and
            source["experiment_overlay_only"] is True and
            overlay["source_head"] == SOURCE_HEAD and overlay["unsigned_diagnostic"] is True and
            overlay["production_and_policy_unchanged"] is True and
            history["source_head"] == SOURCE_HEAD and
            history["android_gradle_jni_module_diff_empty"] is True and
            graph["code_head"] == SOURCE_HEAD and graph["exit_code"] == 0,
            "Source continuity/overlay not reviewed")
    require(preserve["apk_sha256"] == APK_SHA256 and
            preserve["contains_unsigned_apk"] is True and
            preserve["contains_private_key"] is False and
            preserve["recovered_copy_verified"] is True and
            preserve["archive_crc_valid"] is True and
            preserve["verified_members"] == preserve["members"] == 58 and
            isinstance(preserve["sha256"], str) and HEX.fullmatch(preserve["sha256"]),
            "Candidate private preservation unsupported")
    require(compare["historical_unsigned_apk_sha256"] == HISTORICAL_SHA256 and
            compare["candidate_apk_sha256"] == APK_SHA256 and
            compare["historical_apk_available"] is False and
            compare["matches_historical_apk_sha256"] is False and
            compare["elf_inventory_matches"] is True and
            compare["unchanged_elf"] == 96 and len(compare["elf_differences"]) == 1 and
            compare["elf_differences"][0]["member"] == JNI_PATH and
            compare["elf_differences"][0]["candidate_sha256"] == JNI_SHA256 and
            compare["historical_contract_modified"] is False and
            all(v["same_components"] is True and not v["added"] and not v["removed"]
                for v in compare["dependency_graph_comparison"].values()) and
            len(compare["dependency_graph_comparison"]) == 4,
            "Historical comparison cannot establish candidate identity")
    require(audit["apk_sha256"] == APK_SHA256 and
            all(audit["summary"][k] == v for k, v in {
                "elf_total": 97, "android_arm64": 96, "arm64_4k_pass": 96,
                "arm64_16k_pass": 96, "other_machine": 1,
                "missing_needed": 0, "strong_unresolved": 0, "version_mismatch": 0}.items()),
            "Candidate native audit summary mismatch")
    expected = {}
    for row in audit["libraries"]:
        path = row["path"]
        require(type(path) is str and path.startswith(APK_NAME + "!") and
                HEX.fullmatch(row["sha256"]) is not None and
                row["machine"] in ("EM_AARCH64", "EM_X86_64"), "Malformed ELF audit entry")
        member = path[len(APK_NAME)+1:]
        require(member not in expected and
                member.count("!") <= 1 and
                all(part and part not in (".", "..") and "\\" not in part
                    for part in member.replace("!", "/").split("/")),
                "Duplicate or unsafe ELF audit member")
        expected[member] = (row["sha256"], row["machine"])
        if row["machine"] == "EM_AARCH64":
            require(row["load_4k"] is True and row["load_16k"] is True and
                    not row["missing_needed_api24"] and
                    not row["strong_unresolved_api24"] and
                    not row["version_provider_mismatches_api24"],
                    "AArch64 ELF failed static checks")
    require(len(expected) == 97 and
            sum(arch == "EM_AARCH64" for _, arch in expected.values()) == 96 and
            expected.get(JNI_PATH) == (JNI_SHA256, "EM_AARCH64"),
            "Candidate native inventory or JNI invalid")
    require(receipt["packaged_rebuilt_elf"] == PINNED_ELF and
            all(sum(name.endswith("!" + "chaquopy/lib/" + lib) and
                    digest == sha and arch == "EM_AARCH64"
                    for name, (digest, arch) in expected.items()) == 1
                for lib, sha in PINNED_ELF.items()), "Pinned rebuilt ELF no longer packaged")
    require(acceptance["status"] == "STATIC_CLEAN_PENDING_ANDROID" and
            acceptance["arm64_elf"] == 96 and acceptance["non_target_payloads"] == 1 and
            acceptance["blockers"] == [] and acceptance["runtime_required"] is True and
            acceptance["distribution_allowed"] is False,
            "APK candidate static acceptance invalid")
    require(diagnostic["apk_sha256"] == APK_SHA256 and
            diagnostic["bytes"] == APK_BYTES and diagnostic["zip_crc"] == "passed" and
            diagnostic["distribution_allowed"] is False and
            diagnostic["manifest"]["validation"] == "passed" and
            diagnostic["manifest"]["package"] == "io.github.jose22yt.flexygram.diagnostic" and
            "android.permission.INTERNET" not in diagnostic["manifest"]["permissions"] and
            diagnostic["compiled_isolation"]["api_id_zero"] is True and
            diagnostic["compiled_isolation"]["api_hash_empty"] is True and
            diagnostic["variant_policy"]["all_capabilities_disabled"] is True and
            diagnostic["all_translation_gates_passed"] is True,
            "APK candidate Diagnostic safety gates invalid")
    require(len(guards["guards"]) == 3 and
            guards["packaged_text_matches_linked"] is True and
            all(x["instructions"] == ["ret"] and x["body_absent"] is True
                for x in guards["guards"]) and guards["runtime_execution"] is False,
            "Candidate native JNI guards invalid")
    for name in ("native-231.json", "native-231-opt.json"):
        gate = r[name]
        require(gate["status"] == "PASS" and gate["tests_run"] == 231 and
                gate["passed"] == 231 and gate["minimum_required"] == 231 and
                all(gate[k] == 0 for k in ("failures", "errors", "skipped",
                                            "expected_failures", "unexpected_successes")) and
                gate["discovery_incomplete"] is False, "Incomplete candidate gate: " + name)
    require(lab["android_executed"] is False and lab["apk_installed"] is False and
            lab["offline_boot_validated"] is False,
            "New Android runtime evidence requires separate review")
    return expected


def inspect_private_apk(path: Path, expected: dict):
    regular_file(path)
    require(path.name == APK_NAME and path.stat().st_size == APK_BYTES and
            file_sha(path) == APK_SHA256, "Physical APK size/name/SHA256 mismatch")
    found = {}
    with zipfile.ZipFile(path) as outer:
        entries = outer.namelist()
        require(len(entries) == len(set(entries)) and
                outer.testzip() is None, "APK ZIP duplicates or failed CRC")
        require("AndroidManifest.xml" in entries, "Missing APK manifest")
        for info in outer.infolist():
            name = info.filename
            require(not name.startswith("/") and "\\" not in name and
                    all(p and p not in (".", "..") for p in name.rstrip("/").split("/")),
                    "Unsafe APK ZIP path")
            require(stat.S_IFMT(info.external_attr >> 16) not in
                    (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO),
                    "Unsafe APK ZIP member type")
            upper = name.upper()
            require(not (upper.startswith("META-INF/") and
                    (upper.endswith((".RSA", ".DSA", ".EC", ".SF")) or
                     upper == "META-INF/MANIFEST.MF")),
                    "JAR-signed APK cannot be reviewed as unsigned")
            # Chaquopy also places 12 reviewed ELF directly in bootstrap-native assets.
            # Scan every flat native member; the exact pinned inventory below
            # rejects anything unreviewed rather than broadening an allowlist.
            if name.endswith(".so"):
                found[name] = outer.read(name)
        with path.open("rb") as stream:
            stream.seek(max(0, outer.start_dir - 16))
            require(stream.read(16) != b"APK Sig Block 42", "Unexpected APK signing block")
        for nested_name in NESTED:
            require(nested_name in entries, "Missing nested Python archive")
            with zipfile.ZipFile(BytesIO(outer.read(nested_name))) as nested:
                inner_names = nested.namelist()
                require(len(inner_names) == len(set(inner_names)) and
                        nested.testzip() is None, "Nested ZIP duplicates or CRC failure")
                for info in nested.infolist():
                    name = info.filename
                    require(not name.startswith("/") and "\\" not in name and
                            all(p and p not in (".", "..") for p in name.rstrip("/").split("/")),
                            "Unsafe nested ZIP member")
                    require(stat.S_IFMT(info.external_attr >> 16) not in
                            (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO),
                            "Unsafe nested ZIP member type")
                    if name.endswith(".so"):
                        found[nested_name + "!" + name] = nested.read(name)
    require(set(found) == set(expected), "Candidate physical APK ELF inventory mismatch")
    arm64 = 0
    for name, payload in found.items():
        digest, machine = expected[name]
        require(hashlib.sha256(payload).hexdigest() == digest,
                "Physical ELF digest does not match reviewed audit: " + name)
        elf_alignment(payload, machine)
        arm64 += machine == "EM_AARCH64"
    require(arm64 == 96, "Expected 96 AArch64 ELF in physical candidate")
    return {"status": "CANDIDATE_BYTES_STATICALLY_VERIFIED_PENDING_ANDROID",
            "apk_sha256": APK_SHA256, "apk_bytes": APK_BYTES,
            "elf_total": 97, "arm64": arm64,
            "signed": False, "installed": False,
            "android_runtime_validated": False, "distribution_allowed": False,
            "historical_contract_modified": False}


def review(evidence: Path = EVIDENCE, apk: Path | None = None):
    records = check_index(evidence)
    expected = review_records(records)
    if apk is not None:
        return inspect_private_apk(apk, expected)
    return {"status": "CANDIDATE_METADATA_REVIEWED_BYTES_NOT_VERIFIED",
            "apk_sha256": APK_SHA256, "evidence_files": 44,
            "elf_hashes_reported": len(expected), "physical_apk_checked": False,
            "signed": False, "installed": False, "android_runtime_validated": False,
            "distribution_allowed": False, "historical_contract_modified": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    parser.add_argument("--apk", type=Path, help="Actual PRIVATE unsigned candidate APK")
    a = parser.parse_args(argv)
    try:
        print(json.dumps(review(a.evidence, a.apk), sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile,
            json.JSONDecodeError, struct.error) as exc:
        print(json.dumps({"status": "BLOCKED",
                          "blocker": "CANDIDATE_METADATA_OR_BYTES_UNVERIFIED",
                          "error_class": type(exc).__name__,
                          "signed": False, "android_runtime_validated": False,
                          "distribution_allowed": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
