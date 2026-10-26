#!/usr/bin/env python3
"""Fail closed on incomparable runs; never turn synthetic fixtures into device results."""
import argparse
import json
import math
import re
from pathlib import Path
from .metrics import summary

ENVIRONMENT_KEYS = ('device_pair_id', 'build', 'display_size', 'density', 'font_scale',
                    'window_animation_scale', 'transition_animation_scale', 'animator_duration_scale',
                    'theme', 'cache_state', 'conversation_fixture', 'workload_id', 'music_state',
                    'refresh_profile', 'installation_state', 'test_session_state', 'thermal_policy',
                    'battery_policy')
REQUIRED_LABELS = {'exteraless', 'alpha1271', 'candidate'}


def validate(report):
    errors = []
    if report.get('schema') != 1 or report.get('evidence') != 'test_device':
        errors.append('A real test-device report is required; synthetic evidence cannot qualify')
    env = report.get('environment', {})
    for key in ENVIRONMENT_KEYS:
        if env.get(key) in (None, '', 'unknown', 'unverified'):
            errors.append('Missing environment condition: ' + key)
    if not report.get('prepared_test_device'):
        errors.append('Missing operator test-device attestation')
    if not re.fullmatch('[0-9a-f]{40}', str(report.get('source_commit', ''))):
        errors.append('Missing full source provenance')
    captures = report.get('captures', [])
    if len(captures) < 20:
        errors.append('At least20 valid repetitions are required for acceptance comparison')
    for capture in captures:
        metric = capture.get('frames', {}).get('duration_ms', {})
        startup_only = report.get('scenario') == 'cold_start' and capture.get('startup_ms') is not None and metric.get('count') == 0
        for key in (() if startup_only else ('median', 'p95', 'min', 'max')):
            value = metric.get(key)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                errors.append('Invalid summary metric: ' + key)
        if capture.get('startup_ms') is not None:
            value = capture['startup_ms']
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                errors.append('Invalid startup metric')
        if capture.get('frames', {}).get('duration_ms', {}).get('count', 0) == 0 and not startup_only:
            errors.append('Empty frame capture')
        if capture.get('frames', {}).get('unbudgeted_frame_count', 1):
            errors.append('Per-frame refresh budget unavailable')
        for point in ('memory_before', 'memory_after'):
            for value in capture.get(point, {}).values():
                if value is not None and (isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0):
                    errors.append('Invalid memory snapshot')
        health = capture.get('health', {})
        if not health.get('eligible', False):
            errors.append('Thermal/battery conditions unavailable or outside declared bounds')
        for value in capture.get('frames', {}).get('frames', []):
            duration = value.get('duration_ms')
            if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration < 0:
                errors.append('Invalid numerical metric')
    return sorted(set(errors))


def compare(reports, cohort="legacy"):
    if cohort not in ("legacy", "navigation2", "universal3"):
        raise ValueError("Unknown comparison cohort")
    errors = []
    labels = [r.get('label') for r in reports]
    required = REQUIRED_LABELS if cohort == 'legacy' else {'exteraless', 'alpha1275', 'candidate'} if cohort == 'universal3' else {'exteraless', 'alpha1272', 'pr92', 'candidate'}
    if len(reports) != len(required) or set(labels) != required:
        errors.append('Exactly one report per cohort label required: ' + ','.join(sorted(required)))
    if cohort in ('navigation2', 'universal3'):
        pinned = {'exteraless':'1ad6a60a6834ffca722b1a22f4fba27ecb29a061',
                  'alpha1272':'8619ba40fbd8fd9d9d898ff307fb0c0716661254',
                  'pr92':'340cd323f5f5809abc746507b2e252da71298720'}
        if cohort == 'universal3':
            pinned = {'exteraless':'1ad6a60a6834ffca722b1a22f4fba27ecb29a061','alpha1275':'8c47e5532a600f9a8b4ccbfdac5090d09a1075a0'}
        modes = [r.get('environment', {}).get('build_mode') for r in reports]
        if any(m in (None, '', 'unknown', 'unverified') for m in modes) or len(set(modes)) != 1:
            errors.append('Verified equal build modes required')
        for report in reports:
            if report.get('label') in pinned and report.get('source_commit') != pinned[report['label']]:
                errors.append('Incorrect source for pinned cohort: ' + report['label'])
            if report.get('label') == 'candidate' and report.get('source_commit') in pinned.values():
                errors.append('Candidate must identify its own source revision')
    for report in reports:
        errors += [str(report.get('label')) + ': ' + e for e in validate(report)]
    if reports:
        first = reports[0]
        for report in reports[1:]:
            if report.get('scenario') != first.get('scenario'):
                errors.append('Different scenarios')
            for key in ENVIRONMENT_KEYS:
                if report.get('environment', {}).get(key) != first.get('environment', {}).get(key):
                    errors.append('Different environment: ' + key)
        intervals = [sorted({k for c in r.get('captures', []) for k in c.get('frames', {}).get('interval_ms_histogram', {})}) for r in reports]
        if any(x != intervals[0] for x in intervals[1:]):
            errors.append('Different observed refresh intervals; no fixed60Hz assumption permitted')
        def proportions(report):
            counts = {}
            for capture in report.get('captures', []):
                for key, value in capture.get('frames', {}).get('interval_ms_histogram', {}).items():
                    counts[str(key)] = counts.get(str(key), 0) + value
            total = sum(counts.values())
            return {k: v / total for k, v in counts.items()} if total else {}
        profiles = [proportions(report) for report in reports]
        if any(abs(profile.get(key, 0) - profiles[0].get(key, 0)) > .05
               for profile in profiles[1:] for key in set(profile) | set(profiles[0])):
            errors.append('Observed refresh proportions differ by more than5 percentage points')

    if errors:
        return {'comparable': False, 'reasons': sorted(set(errors)), 'superiority': 'NOT_ESTABLISHED', 'rows': []}
    rows = []
    for report in reports:
        captures = report['captures']
        medians = [c['frames']['duration_ms']['median'] for c in captures if c['frames']['duration_ms']['median'] is not None]
        p95s = [c['frames']['duration_ms']['p95'] for c in captures if c['frames']['duration_ms']['p95'] is not None]
        starts = [c['startup_ms'] for c in captures if c.get('startup_ms') is not None]
        rows.append({'label': report['label'], 'source_commit': report['source_commit'],
                     'repetitions': len(captures), 'sample_medians_ms': summary(medians),
                     'sample_p95s_ms': summary(p95s), 'startup_ms': summary(starts),
                     'over_interval_frames': sum(c['frames']['over_interval_frames'] for c in captures),
                     'frame_count': sum(c['frames']['duration_ms']['count'] for c in captures),
                     'memory_before_pss_kib': summary([c['memory_before']['total_pss_kib'] for c in captures if c.get('memory_before', {}).get('total_pss_kib') is not None]),
                     'memory_after_pss_kib': summary([c['memory_after']['total_pss_kib'] for c in captures if c.get('memory_after', {}).get('total_pss_kib') is not None]),
                     'touch_to_visible_ms': None, 'surfaceflinger_jank': None})
    return {'comparable': True, 'reasons': [], 'rows': rows,
            'superiority': 'NOT_AUTOMATICALLY_ESTABLISHED',
            'caution': 'Median of repetition p95 is not a pooled p95; thermal/order/cache confounding still needs review.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('reports', type=Path, nargs='+')
    p.add_argument('--cohort', choices=['legacy','navigation2','universal3'], default='legacy')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = compare([json.loads(f.read_text()) for f in a.reports], a.cohort)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return 0 if result['comparable'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
