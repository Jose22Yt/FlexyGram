#!/usr/bin/env python3
"""Read-only review of the unsigned P0.4c APK evidence; NEVER authorizes signing.

Produces an unsigned *candidate descriptor*, not an Android runtime contract.
The historical signed v1 lab contract remains untouched and authoritative.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/security-p04c/evidence-work-20261019"
HISTORICAL = ROOT / "docs/security-p04c/evidence-16k-experimental/wheel-reproducibility.json"
LAB_V1 = ROOT / "tests/native_compatibility/android_lab/contract.json"
PENDING_IDENTITY = ROOT / "docs/security-p04c/signing-v2/identity.pending.json"
APK_SHA256 = "ddb7b017838a2a13991ac09154bbf252a11d62326e9a588349ca03c115e01699"
APK_BYTES = 113080783
LIBRARIES = frozenset(("libexslt.so", "libfreetype.so", "libxml2.so", "libxslt.so"))
NEEDED = frozenset((
    "unsigned-apk-receipt.json", "apk-native-audit.json", "apk-native-acceptance.json",
    "apk-diagnostic-check.json", "reproduction-receipt.json", "abi-final-wheels.json",
    "experimental-wheels-manifest.json", "production-rejection.json",
    "lab-input-rejection.json", "lab-inventory.json", "native-linked-guards.json",
    "overlay.json", "apk-signature.log", "native-all.json",
    "native-all-optimized.json",
))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            d.update(data)
    return d.hexdigest()


def check_evidence_files(folder: Path) -> int:
    require(folder.is_dir() and not folder.is_symlink(), "Evidence directory missing or unsafe")
    inventory = read_json(folder / "evidence-sha256.json")
    files = inventory["evidence_files"]
    require(isinstance(files, dict) and NEEDED <= files.keys(), "Evidence inventory incomplete")
    require(len(files) >= len(NEEDED), "Evidence inventory too small")
    for name, digest in files.items():
        require(isinstance(name, str) and name and Path(name).name == name and
                name not in (".", "..") and not any(ch in name for ch in ("/", "\\", "\x00")),
                "Unsafe evidence filename")
        require(isinstance(digest, str) and len(digest) == 64 and
                all(c in "0123456789abcdef" for c in digest), "Bad evidence digest")
        path = folder / name
        require(not path.is_symlink() and path.is_file(), "Evidence file missing/unsafe: " + name)
        require(sha256(path) == digest, "Evidence digest mismatch: " + name)
    return len(files)


def verify(folder: Path = EVIDENCE) -> dict:
    count = check_evidence_files(folder)
    apk = read_json(folder / "unsigned-apk-receipt.json")
    repro = read_json(folder / "reproduction-receipt.json")
    wheel_manifest = read_json(folder / "experimental-wheels-manifest.json")
    abi = read_json(folder / "abi-final-wheels.json")
    accept = read_json(folder / "apk-native-acceptance.json")
    audit = read_json(folder / "apk-native-audit.json")
    diagnostic = read_json(folder / "apk-diagnostic-check.json")
    production = read_json(folder / "production-rejection.json")
    rejected = read_json(folder / "lab-input-rejection.json")
    inventory = read_json(folder / "lab-inventory.json")
    guards = read_json(folder / "native-linked-guards.json")
    overlay = read_json(folder / "overlay.json")
    historic = read_json(HISTORICAL)
    previous = read_json(LAB_V1)
    signing = read_json(PENDING_IDENTITY)

    require(previous["apk_sha256"] != APK_SHA256 and
            previous["apk_sha256"] == signing["historical_apk_sha256"] and
            previous["certificate_sha256"] == signing["historical_certificate_sha256"],
            "Legacy v1 contract unexpectedly changed")
    require(signing["status"] == "BLOCKED_CUSTODY_NOT_CREATED" and
            signing["certificate_sha256"] is None and
            signing["private_key_generated"] is False and
            signing["apk_signing_authorized"] is False,
            "No unsigned proposal allowed once signing state changes; request new review")
    require(apk["status"] == "BUILT_UNSIGNED_STATIC_VERIFIED" and
            apk["apk_sha256"] == APK_SHA256 and apk["apk_bytes"] == APK_BYTES and
            apk["build_result"] == "BUILD SUCCESSFUL" and
            apk["signature"] == "absent" and apk["apksigner_exit"] != 0 and
            apk["apk_signing_block"] is False and apk["jar_signature_entries"] is False and
            apk["signing_key_loaded_or_generated"] is False and
            apk["zip_crc_valid"] is True and apk["zipalign_16k"] is True and
            apk["jni_and_chaquopy_built"] is True and
            all(apk[k] is False for k in ("installed", "distributed", "android_runtime_validated")),
            "Unsigned APK receipt or signing status changed")
    require(overlay["source_head"] == apk["source_head"] and
            overlay["unsigned_diagnostic"] is True and
            overlay["production_and_policy_unchanged"] is True,
            "Build overlay provenance or policy changed")
    require(repro["status"] == "REPRODUCIBLE_STATIC_OUTPUTS_ONLY" and
            repro["runs"] == 2 and repro["input_original_wheels"] == 18 and
            all(repro[k] is False for k in ("apk_signed", "android_runtime_validated", "merged")),
            "Rebuild provenance invalid")

    elf = apk["packaged_elf_sha256"]
    require(set(elf) == LIBRARIES and elf == repro["elf_sha256"], "Packaged ELF hashes differ from A/B")
    rows = wheel_manifest["wheels"]
    require(len(rows) == 18 and len({r["filename"] for r in rows}) == 18 and
            len({r["original_filename"] for r in rows}) == 18 and
            sum(r["rebuilt"] is True for r in rows) == 3 and
            all(type(r["rebuilt"]) is bool for r in rows), "Wheel inventory invalid")
    require({r["filename"]: r["sha256"] for r in rows} == repro["wheel_sha256"],
            "Rebuilt wheel inventory differs from A/B")
    historic_wheels = {r["filename"]: r["sha256"] for r in historic["rebuilt"]}
    require({r["filename"]: r["sha256"] for r in rows if r["rebuilt"]} == historic_wheels,
            "Three rebuilt wheel pins differ from historical approval")
    require(len(abi) == 4 and {r["library"].rsplit("/", 1)[-1] for r in abi} == LIBRARIES and
            all(r["static_abi_pass"] is True and r["runtime_validated"] is False and
                r["contract"]["after_sha256"] == elf[r["library"].rsplit("/", 1)[-1]] and
                not r["contract"]["blockers"] for r in abi), "Final wheel ABI incomplete")

    summary = audit["summary"]
    require(audit["apk_sha256"] == APK_SHA256 and
            all(summary[k] == v for k, v in {
                "elf_total": 97, "android_arm64": 96, "arm64_4k_pass": 96,
                "arm64_16k_pass": 96, "other_machine": 1, "missing_needed": 0,
                "strong_unresolved": 0, "version_mismatch": 0}.items()),
            "Native audit summary changed")
    require(len(audit["libraries"]) == 97, "Native audit entries incomplete")
    aarch64 = [x for x in audit["libraries"] if x["machine"] == "EM_AARCH64"]
    require(len(aarch64) == 96 and all(
        x["load_4k"] is True and x["load_16k"] is True and
        not x["missing_needed_api24"] and not x["strong_unresolved_api24"] and
        not x["version_provider_mismatches_api24"] for x in aarch64),
        "Per-library 4K/16K/API24 audit failed")
    for name, digest in elf.items():
        matches = [x for x in aarch64 if x["path"].endswith("!chaquopy/lib/" + name)]
        require(len(matches) == 1 and matches[0]["sha256"] == digest,
                "Native ELF in APK does not match rebuild: " + name)
    require(accept["status"] == "STATIC_CLEAN_PENDING_ANDROID" and
            accept["arm64_elf"] == 96 and accept["non_target_payloads"] == 1 and
            accept["blockers"] == [] and accept["distribution_allowed"] is False and
            accept["runtime_required"] is True, "Static acceptance changed")
    require(diagnostic["apk_sha256"] == APK_SHA256 and diagnostic["bytes"] == APK_BYTES and
            diagnostic["zip_crc"] == "passed" and diagnostic["distribution_allowed"] is False and
            diagnostic["manifest"]["validation"] == "passed" and
            diagnostic["manifest"]["package"] == previous["target_package"] and
            "android.permission.INTERNET" not in diagnostic["manifest"]["permissions"] and
            diagnostic["compiled_isolation"]["api_id_zero"] is True and
            diagnostic["compiled_isolation"]["api_hash_empty"] is True and
            diagnostic["variant_policy"]["all_capabilities_disabled"] is True and
            diagnostic["all_translation_gates_passed"] is True,
            "Diagnostic APK safety gate changed")
    require(len(guards["guards"]) == 3 and guards["packaged_text_matches_linked"] is True and
            all(g["instructions"] == ["ret"] and g["body_absent"] is True for g in guards["guards"]) and
            guards["runtime_execution"] is False, "JNI guards changed")
    require(production["expected_failure"] is True and
            production["marker_present"] is True and
            production["production_apk_exists"] is False and
            rejected["expected_block"] is True and
            rejected["result"]["android_executed"] is False and
            inventory["android_executed"] is False,
            "Production or Android lab evidence contradicts unsigned-only state")
    require("DOES NOT VERIFY" in (folder / "apk-signature.log").read_text(),
            "Expected unsigned APK signature failure missing")
    for name in ("native-all.json", "native-all-optimized.json"):
        run = read_json(folder / name)
        require(run["status"] == "PASS" and run["passed"] == run["tests_run"] and
                run["failures"] == 0 and run["errors"] == 0 and run["skipped"] == 0,
                "Native host gate failed: " + name)
    return {
        "schema": 1, "status": "UNSIGNED_EVIDENCE_REVIEWED_SIGNING_BLOCKED",
        "kind": "proposal_only_not_android_lab_contract",
        "unsigned_apk_sha256": APK_SHA256, "unsigned_apk_bytes": APK_BYTES,
        "source_head": apk["source_head"], "native_elf_sha256": elf,
        "reviewed_original_wheels": 18, "reviewed_rebuilt_wheels": 3,
        "reviewed_arm64_elf": 96, "evidence_files_verified": count,
        "historical_lab_contract_preserved": True,
        "signed_apk_sha256": None, "signed_apk_bytes": None,
        "certificate_sha256": None, "signed_runner_sha256": None,
        "signing_authorized": False, "android_runtime_validated": False,
        "distribution_allowed": False, "lab_profiles_completed": 0,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE,
                        help="Only a verified local copy of the published evidence")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify(args.evidence), indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "error_class": type(exc).__name__,
                          "signed_apk_sha256": None, "android_runtime_validated": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
