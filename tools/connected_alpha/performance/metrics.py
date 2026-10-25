"""Reuse existing parsers; retain per-frame refresh/deadline evidence separately."""
import csv
import math
import statistics
from collections import Counter
from tools.connected_alpha.measure_login import frame_times
from tools.connected_alpha.measure_music import stats as legacy_frame_stats

MAX_TIME = 9223372036854775807


def summary(values):
    if not values:
        return {'count': 0, 'median': None, 'p95': None, 'min': None, 'max': None}
    if any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError('Nonfinite/negative metrics cannot be compared')
    ordered = sorted(values)
    return {'count': len(values), 'median': statistics.median(values),
            'p95': ordered[math.ceil(.95 * len(values)) - 1], 'min': ordered[0], 'max': ordered[-1]}


def gfxinfo(text, fallback_hz=None):
    if fallback_hz is not None and (not math.isfinite(fallback_hz) or not 1 <= fallback_hz <= 1000):
        raise ValueError('Refresh rate must be finite and explicitly verified')
    header = None
    records = []
    identities = set()
    rejected = Counter()
    window_section = -1
    for cells in csv.reader(text.splitlines()):
        if all(k in cells for k in ('Flags', 'IntendedVsync', 'FrameCompleted')):
            header = {k: i for i, k in enumerate(cells)}
            window_section += 1
            continue
        if header is None or not cells or not cells[0].strip().isdigit():
            continue
        try:
            def number(key):
                return int(cells[header[key]])
            if number('Flags') != 0:
                rejected['flagged'] += 1
                continue
            start, end = number('IntendedVsync'), number('FrameCompleted')
            if not 0 < start < end < MAX_TIME:
                rejected['incomplete_or_invalid'] += 1
                continue
            # Identical sections may be repeated by tools. Deduplicate only exact frame identity.
            identity = (window_section, start, end, tuple(cells))
            if identity in identities:
                rejected['duplicate'] += 1
                continue
            identities.add(identity)
            interval = number('FrameInterval') if 'FrameInterval' in header else None
            if interval is not None and not 1_000_000 <= interval <= 1_000_000_000:
                interval = None
            budget = interval / 1e6 if interval else 1000 / fallback_hz if fallback_hz else None
            deadline = number('FrameDeadline') if 'FrameDeadline' in header else None
            if deadline is not None and not start < deadline < MAX_TIME:
                deadline = None
            # Delegate duration semantics to the existing login parser, using its validated minimal row.
            duration = frame_times(f'Flags,IntendedVsync,FrameCompleted\n0,{start},{end}')[0]
            records.append({'window_section': window_section, 'duration_ms': duration, 'budget_ms': budget,
                            'budget_source': 'FrameInterval' if interval else 'operator_verified_hz' if fallback_hz else None,
                            'deadline_missed': end > deadline if deadline else None})
        except (ValueError, IndexError, KeyError):
            rejected['malformed'] += 1
    durations = [r['duration_ms'] for r in records]
    known = [r for r in records if r['budget_ms'] is not None]
    deadlines = [r['deadline_missed'] for r in records if r['deadline_missed'] is not None]
    return {'frames': records, 'duration_ms': summary(durations), 'rejected': dict(rejected),
            'budgeted_frame_count': len(known), 'unbudgeted_frame_count': len(records) - len(known),
            'over_interval_frames': sum(r['duration_ms'] > r['budget_ms'] for r in known),
            'deadline_observed_count': len(deadlines), 'deadline_missed_frames': sum(deadlines),
            'interval_ms_histogram': dict(Counter(round(r['budget_ms'], 5) for r in known)),
            'jank': 'NOT_MEASURED_BY_GFXINFO', 'touch_to_visible_ms': None,
            'duration_semantics': 'IntendedVsync to FrameCompleted; not input latency',
            'legacy_summary': legacy_frame_stats(durations, 1000 / fallback_hz) if durations and fallback_hz else None}
