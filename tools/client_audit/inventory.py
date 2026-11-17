#!/usr/bin/env python3
"""Read-only inventory and candidate scan; matches are review prompts, not proven defects."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ROOTS = ['TMessagesProj/src/main', 'TMessagesProj/jni', 'TMessagesProj_Modules']
CODE = {'.java', '.kt', '.c', '.cc', '.cpp', '.h', '.hpp', '.py', '.js'}
PATTERNS = {
    'sync_preferences': re.compile(r'\.commit\s*\('),
    'thread_wait': re.compile(r'\b(?:await|join|wait)\s*\('),
    'static_collection': re.compile(r'\bstatic\b[^;\n]*(?:HashMap|ArrayList|SparseArray|Set<|Map<|List<)'),
    'scheduled_work': re.compile(r'\b(?:postDelayed|postFrameCallback|runOnUIThread)\s*\('),
    'whole_file_read': re.compile(r'\b(?:readBytes|readText|readAllBytes)\s*\('),
    'explicit_gc': re.compile(r'\bSystem\.gc\s*\('),
    'conflict_marker': re.compile(r'^(?:<<<<<<<|=======|>>>>>>>)', re.MULTILINE),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', *ROOTS], cwd=ROOT).decode().split('\0')
    extensions, areas, totals = collections.Counter(), collections.Counter(), collections.Counter()
    candidates, unavailable = [], []
    manifest = hashlib.sha256()
    for name in sorted(filter(None, tracked)):
        path = ROOT / name
        if path.suffix not in CODE | {'.xml'}:
            continue
        if not path.is_file():
            unavailable.append(name)
            continue
        data = path.read_bytes()
        extensions[path.suffix] += 1
        parts = name.split('/')
        if name.startswith('TMessagesProj/src/main/java/') or name.startswith('TMessagesProj/src/main/kotlin/'):
            area = '/'.join(parts[4:7])
        else:
            area = '/'.join(parts[:4])
        areas[area] += 1
        manifest.update(name.encode() + b'\0' + hashlib.sha256(data).digest())
        if path.suffix in CODE:
            text = data.decode('utf-8', errors='replace')
            matches = {key: len(list(pattern.finditer(text))) for key, pattern in PATTERNS.items()}
            matches = {key: value for key, value in matches.items() if value}
            if matches:
                candidates.append({'file': name, 'matches': matches})
                totals.update(matches)
    stage = subprocess.check_output(['git', 'ls-files', '--stage', '--', *ROOTS], cwd=ROOT, text=True)
    submodules = [line.split('\t', 1)[1] for line in stage.splitlines() if line.startswith('160000 ')]
    report = {
        'scope': 'tracked application/native/module code and XML; untracked/generated/submodule contents excluded',
        'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'working_tree_scan': True,
        'files_indexed': sum(extensions.values()),
        'extension_counts': dict(sorted(extensions.items())),
        'area_counts': dict(sorted(areas.items())),
        'content_manifest_sha256': manifest.hexdigest(),
        'candidate_totals': dict(sorted(totals.items())),
        'candidates_are_not_findings': True,
        'candidate_files': candidates,
        'unavailable_tracked_paths': unavailable,
        'submodule_boundaries_not_scanned': submodules,
        'manual_review_and_device_validation': 'separate; this report is not an exhaustive semantic/security audit',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ['files_indexed', 'extension_counts', 'candidate_totals', 'submodule_boundaries_not_scanned']}))


if __name__ == '__main__':
    main()
