#!/usr/bin/env python3
"""Check real unsigned Diagnostic APK bytes against approved evidence; no signing."""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import stat
import struct
import zipfile

import review_unsigned_contract as review

NESTED = ("assets/chaquopy/requirements-common.imy",
          "assets/chaquopy/stdlib-arm64-v8a.imy")


class MissingPrivateApkError(ValueError):
    """Missing bytes are a recovery blocker, never a successful evidence review."""


def elf_alignment(data: bytes, machine: str) -> None:
    review.require(data[:6] == b"\x7fELF\x02\x01" and len(data) >= 64, "Bad ELF64")
    m = struct.unpack_from("<H", data, 18)[0]
    review.require(m == (183 if machine == "EM_AARCH64" else 62), "ELF architecture mismatch")
    if m != 183:
        return
    start = struct.unpack_from("<Q", data, 32)[0]
    stride, count = struct.unpack_from("<HH", data, 54)
    review.require(stride >= 56 and 0 < count <= 2048 and
                   start + stride * count <= len(data), "ELF program header table invalid")
    loads = 0
    for i in range(count):
        kind, flags, offset, vaddr, paddr, size, mem, align = struct.unpack_from(
            "<IIQQQQQQ", data, start + i * stride)
        if kind == 1:
            loads += 1
            review.require(align >= 16384 and not align & (align - 1) and
                           (vaddr - offset) % align == 0 and
                           size <= mem and offset + size <= len(data),
                           "APK ELF 16 KB PT_LOAD invalid")
    review.require(loads > 0, "APK ELF lacks PT_LOAD")


def verify(apk: Path, evidence: Path = review.EVIDENCE) -> dict:
    review.verify(evidence)
    # Keep unsafe/symlink inputs distinct from an absent private build output.
    if not apk.exists() and not apk.is_symlink() and not any(p.is_symlink() for p in apk.parents):
        raise MissingPrivateApkError('Private unsigned APK unavailable')
    review.require(apk.is_file() and not apk.is_symlink() and
                   not any(p.is_symlink() for p in apk.parents), "Missing or unsafe APK")
    receipt = review.read_json(evidence / "unsigned-apk-receipt.json")
    review.require(apk.name == receipt["apk_filename"] and
                   apk.stat().st_size == review.APK_BYTES and
                   review.sha256(apk) == review.APK_SHA256,
                   "Private APK SHA256, filename or size mismatch")
    audit = review.read_json(evidence / "apk-native-audit.json")["libraries"]
    review.require(len(audit) == 97, "Audit must contain 97 libraries")
    expected = {}
    for row in audit:
        prefix = apk.name + "!"
        path = row["path"]
        review.require(path.startswith(prefix) and
                       row["machine"] in ("EM_AARCH64", "EM_X86_64"),
                       "Unexpected audited ELF")
        member = path[len(prefix):]
        review.require(member not in expected and member.count("!") <= 1 and
                       all(p and not p.startswith("/") and "\\" not in p and
                           ".." not in p.split("/") for p in member.split("!")),
                       "Unsafe or duplicate audit path")
        expected[member] = (row["sha256"], row["machine"])
    actual = {}
    with zipfile.ZipFile(apk) as outer:
        names = outer.namelist()
        review.require(len(names) == len(set(names)) and outer.testzip() is None,
                       "APK ZIP duplicate path or failed CRC")
        for info in outer.infolist():
            kind = stat.S_IFMT(info.external_attr >> 16)
            review.require(kind not in (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK),
                           "Unsafe APK ZIP member")
        review.require(not any(n.upper().startswith("META-INF/") and
                       (n.upper().endswith((".RSA", ".DSA", ".EC", ".SF")) or
                        n.upper() == "META-INF/MANIFEST.MF") for n in names),
                       "Unexpected JAR signature")
        with apk.open("rb") as file:
            file.seek(max(0, outer.start_dir - 16))
            review.require(file.read(16) != b"APK Sig Block 42",
                           "Unexpected APK signing block")
        for name in names:
            if name.startswith("lib/") and name.endswith(".so"):
                actual[name] = outer.read(name)
        for container in NESTED:
            review.require(container in names, "Missing reviewed Python archive")
            with zipfile.ZipFile(BytesIO(outer.read(container))) as nested:
                inner_names = nested.namelist()
                review.require(len(inner_names) == len(set(inner_names)) and
                               nested.testzip() is None, "Nested ZIP invalid")
                for name in inner_names:
                    if name.endswith(".so"):
                        actual[container + "!" + name] = nested.read(name)
    review.require(set(actual) == set(expected), "APK ELF inventory differs from audit")
    count = 0
    for name, payload in actual.items():
        sha, machine = expected[name]
        review.require(hashlib.sha256(payload).hexdigest() == sha,
                       "APK ELF SHA256 mismatch: " + name)
        elf_alignment(payload, machine)
        count += machine == "EM_AARCH64"
    review.require(count == 96, "Expected 96 AArch64 ELF files")
    return {"status": "PRIVATE_UNSIGNED_APK_BYTES_VERIFIED_ONLY",
            "sha256": review.APK_SHA256, "size": review.APK_BYTES,
            "native_entries": len(actual), "arm64_elf": count,
            "signed": False, "installed": False,
            "android_runtime_validated": False, "distribution_allowed": False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apk", type=Path, required=True)
    p.add_argument("--evidence", type=Path, default=review.EVIDENCE)
    args = p.parse_args(argv)
    try:
        print(json.dumps(verify(args.apk, args.evidence), indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "BLOCKED", "error_class": type(exc).__name__,
                          "blocker": "BLOCKED_MISSING_PRIVATE_APK" if isinstance(exc, MissingPrivateApkError) else "VERIFICATION_FAILED",
                          "signed": False, "android_runtime_validated": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
