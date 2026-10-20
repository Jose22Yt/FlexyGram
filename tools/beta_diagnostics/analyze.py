"""Stdlib offline diagnostics. Missing observations never become zero-latency results."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

LIMIT = 64 * 1024 * 1024
OPS = ('startup', 'chat_open', 'chat_close', 'rapid_tap', 'transition_interrupt', 'theme_light', 'theme_dark')
CONDITIONS = ('device_id', 'android_api', 'page_bytes', 'refresh_hz', 'resolution',
              'build_type', 'scenario', 'dataset_id', 'cache_state', 'thermal_state',
              'charging', 'power_save', 'animation_scales', 'navigation', 'theme',
              'event_endpoint', 'protocol', 'observer_lost_events')
TOKEN = re.compile(r'[A-Za-z0-9_-]{1,64}')
PACKAGE = re.compile(r'[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+')
SIGNALS = {
    'java_fatal': r'\bFATAL EXCEPTION\b',
    'anr': r'\bANR in\b|Input dispatching timed out|Application Not Responding',
    'native_crash': r'\bFatal signal\s+\d+|\bSIGSEGV\b|\bSIGABRT\b',
    'native_load': r'UnsatisfiedLinkError|dlopen failed|cannot locate symbol|couldn.t find.*\.so',
    'jni': r'JNI DETECTED ERROR|JNI_ERR|No implementation found for',
    'python': r'com\.chaquo\.python\.PyException|ModuleNotFoundError|ImportError|Fatal Python error',
    'animation': r'Animator has already started|RenderNodeAnimator.*(?:Exception|Error)|IllegalAccessError.*ViewPager',
}
EPOCH = re.compile(r'^\s*(\d+\.\d+)\s+(\d+)\s+(\d+)\s+([VDIWEFAS])\s+([^:]+):\s?(.*)$')
THREAD = re.compile(r'^\s*\d\d-\d\d\s+\d\d:\d\d:\d\d\.\d+\s+(\d+)\s+(\d+)\s+([VDIWEFAS])\s+([^:]+):\s?(.*)$')


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default error may echo private input values.
        print(json.dumps({'status': 'INVALID_ARGUMENTS'}))
        raise SystemExit(2)


class InputError(ValueError):
    """Only fixed developer-defined codes; never payload or subprocess output."""


def require(value, code):
    if not value:
        raise InputError(code)


def strict_json(text):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'DUPLICATE_JSON_KEY')
            out[key] = value
        return out
    def invalid(_): raise ValueError('NONFINITE_JSON')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def read(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= LIMIT, 'INPUT_NOT_BOUNDED_REGULAR_FILE')
    with path.open('rb') as source:
        data = source.read(LIMIT + 1)
    require(len(data) <= LIMIT, 'INPUT_TOO_LARGE')
    return data.decode('utf-8')


def finite(value, low=0):
    return type(value) in (int, float) and math.isfinite(value) and value >= low


def summary(values):
    if not values:
        return {'n': 0, 'p50_ms': None, 'p95_ms': None, 'p99_ms': None, 'max_ms': None}
    data = sorted(values)
    return dict(n=len(data), **{'p' + str(p) + '_ms': data[math.ceil(len(data) * p / 100) - 1] for p in (50, 95, 99)}, max_ms=data[-1])


def logs(text, package, pids, window=None):
    require(PACKAGE.fullmatch(package), 'INVALID_PACKAGE')
    require(all(type(x) is int and x > 0 for x in pids), 'INVALID_PIDS')
    if window is not None:
        require(len(window) == 2 and all(finite(x) for x in window) and window[1] > window[0], 'INVALID_EPOCH_WINDOW')
    counts = dict.fromkeys(SIGNALS, 0)
    parsed = attributed = unparsed = skipped = 0
    choreographer = 0
    for line in text.splitlines():
        match = EPOCH.match(line)
        stamp = None
        if match:
            stamp, pid, tid, level, tag, message = match.groups()
            stamp = float(stamp)
        else:
            match = THREAD.match(line)
            if not match:
                if line and not line.startswith('---------'): unparsed += 1
                continue
            pid, tid, level, tag, message = match.groups()
        parsed += 1
        if window is not None and (stamp is None or not window[0] <= stamp <= window[1]):
            skipped += 1
            continue
        # PID matches capture's known target processes; system evidence needs explicit target identity.
        target = (int(pid) in pids or bool(re.search(
            r'(?:ANR in |Process: |>>> )' + re.escape(package) + r'(?=[:,\s]|$)', message)))
        if not target:
            continue
        attributed += 1
        for category, expression in SIGNALS.items():
            # Do not classify quoted conversation/error text as Android system events.
            if category == 'java_fatal' and not (tag.strip() == 'AndroidRuntime' and message.startswith('FATAL EXCEPTION')):
                continue
            if category == 'anr' and tag.strip() not in ('ActivityManager', 'ActivityTaskManager', 'InputDispatcher', 'WindowManager'):
                continue
            if re.search(expression, message): counts[category] += 1
        if tag.strip() == 'Choreographer':
            skipped_match = re.search(r'\bSkipped (\d+) frames!', message)
            if skipped_match: choreographer += int(skipped_match[1])
    return {'status': 'OBSERVED_LOG_SIGNALS' if attributed else 'NO_ATTRIBUTED_DATA',
            'parsed_lines': parsed, 'unparsed_lines': unparsed, 'attributed_lines': attributed,
            'outside_window_or_undated': skipped, 'epoch_window_scoped': window is not None,
            'signal_counts': counts if attributed else None,
            'choreographer_reported_skipped_frames': choreographer if attributed else None,
            'limits': 'Signals, not unique crash/ANR counts; absence is not proof of stability. No raw messages emitted.'}


def frames(text, refresh_hz, stream=None, window_ns=None):
    require(finite(refresh_hz, 1) and refresh_hz <= 360, 'INVALID_REFRESH_RATE')
    if window_ns is not None:
        require(len(window_ns) == 2 and all(type(x) is int and x >= 0 for x in window_ns) and window_ns[1] > window_ns[0], 'INVALID_FRAME_WINDOW')
    streams, active, header = [], None, None
    for line in text.splitlines():
        if line.strip() == '---PROFILEDATA---':
            if active is None:
                active = {'durations': [], 'deadline_misses': 0, 'deadline_samples': 0, 'excluded_flags': 0, 'invalid_rows': 0, 'duplicates': 0, 'outside_window': 0, 'seen': set()}
                streams.append(active)
            else:
                active = None
            header = None
            continue
        if active is None or not line.strip(): continue
        row = next(csv.reader([line.strip()]))
        if row and row[0] == 'Flags':
            require(len(row) == len(set(row)), 'DUPLICATE_FRAME_COLUMNS')
            header = row
            require(all(x in header for x in ('Flags', 'IntendedVsync', 'FrameCompleted')), 'MISSING_FRAME_COLUMNS')
            continue
        if header is None: continue
        try:
            require(len(row) == len(header), 'FRAME_COLUMN_COUNT')
            values = dict(zip(header, row))
            flags, start, end = [int(values[x]) for x in ('Flags', 'IntendedVsync', 'FrameCompleted')]
            if flags != 0:
                active['excluded_flags'] += 1
                continue
            require(0 < start < end < 2**63 - 1, 'INVALID_FRAME_TIMESTAMP')
            if window_ns is not None and not (window_ns[0] <= start and end <= window_ns[1]):
                active['outside_window'] += 1
                continue
            key = (start, end)
            if key in active['seen']:
                active['duplicates'] += 1
                continue
            deadline = int(values.get('FrameDeadline', '0'))
            active['seen'].add(key)
            active['durations'].append((end - start) / 1e6)
            if start < deadline < 2**63 - 1:
                active['deadline_samples'] += 1
                active['deadline_misses'] += end > deadline
        except (ValueError, OverflowError): active['invalid_rows'] += 1
    require(active is None, 'TRUNCATED_PROFILEDATA')
    if stream is None and len(streams) > 1:
        return {'status': 'MULTIPLE_STREAMS_SELECT_ONE', 'streams': len(streams), 'metrics': None}
    if not streams: return {'status': 'NO_FRAME_DATA', 'streams': 0, 'metrics': None}
    index = 0 if stream is None else stream
    require(type(index) is int and 0 <= index < len(streams), 'INVALID_STREAM_INDEX')
    data = streams[index]
    durations = data.pop('durations')
    data.pop('seen')
    budget = 1000 / refresh_hz
    return {'status': 'FRAME_SAMPLE' if durations else 'NO_VALID_FRAMES', 'stream_index': index,
            'streams': len(streams), 'window_scoped': window_ns is not None, 'refresh_hz': refresh_hz,
            'metrics': dict(summary(durations), budget_ms=budget,
                            over_budget_frames=sum(x > budget for x in durations),
                            over_budget_pct=100 * sum(x > budget for x in durations) / len(durations) if durations else None,
                            frozen_over_700ms=sum(x > 700 for x in durations), **data),
            'presented_fps': None, 'actual_dropped_frames': None,
            'limits': 'IntendedVsync to FrameCompleted sample; not display presentation FPS. Ring buffer may truncate the scenario.'}


def interactions(text):
    pending, terminals, samples = {}, {}, {op: {'requested': 0, 'accepted': 0, 'presented': 0, 'cancelled': 0, 'timeout': 0,
                                               'accept_ms': [], 'present_ms': [], 'cancel_ms': []} for op in OPS}
    last = -1
    for line in text.splitlines():
        if not line.strip(): continue
        event = strict_json(line)
        require(type(event) is dict and set(event) == {'id', 'op', 'phase', 'timestamp_ns', 'clock'}, 'INVALID_EVENT_FIELDS')
        ident, op, phase, stamp = [event[x] for x in ('id', 'op', 'phase', 'timestamp_ns')]
        require(type(ident) is str and TOKEN.fullmatch(ident) and op in OPS, 'INVALID_EVENT_ID_OR_OPERATION')
        require(event['clock'] == 'android_monotonic_ns' and type(stamp) is int and stamp >= last and stamp >= 0, 'INVALID_EVENT_CLOCK')
        last = stamp
        if phase == 'request':
            require(ident not in pending and ident not in terminals, 'DUPLICATE_REQUEST')
            pending[ident] = {'op': op, 'request': stamp}
            samples[op]['requested'] += 1
            continue
        require(ident in pending and pending[ident]['op'] == op, 'ORPHAN_EVENT')
        item, stats = pending[ident], samples[op]
        if phase == 'accepted':
            require('accepted' not in item, 'DUPLICATE_ACCEPTANCE')
            item['accepted'] = stamp
            stats['accepted'] += 1
            stats['accept_ms'].append((stamp - item['request']) / 1e6)
        else:
            require(phase in ('presented', 'cancelled', 'timeout'), 'INVALID_EVENT_PHASE')
            if phase == 'presented':
                require('accepted' in item, 'PRESENTED_WITHOUT_ACCEPTANCE')
                stats['present_ms'].append((stamp - item['request']) / 1e6)
            if phase == 'cancelled':
                stats['cancel_ms'].append((stamp - item['request']) / 1e6)
            stats[phase] += 1
            terminals[ident] = pending.pop(ident)
    for op, stats in samples.items():
        stats['incomplete'] = sum(item['op'] == op for item in pending.values())
        stats['request_to_accept'] = summary(stats.pop('accept_ms'))
        stats['request_to_present'] = summary(stats.pop('present_ms'))
        stats['request_to_cancel'] = summary(stats.pop('cancel_ms'))
    return {'status': 'EVENT_SAMPLE' if pending or terminals else 'NO_EVENT_DATA', 'operations': samples,
            'limits': 'Requires real instrumentation or reviewed external observer. Incomplete/timeout is not proof of ANR or ignored physical touch.'}


def metadata(value):
    require(type(value) is dict and set(value) <= {'schema', 'client', 'apk_sha256', 'source', 'run_id', 'repetition', 'conditions'}, 'INVALID_METADATA_FIELDS')
    require(type(value.get('schema')) is int and value['schema'] == 1 and value.get('client') in ('FlexyGram', 'Exteraless', 'Exteragram'), 'INVALID_METADATA_IDENTITY')
    require(re.fullmatch(r'[0-9a-f]{64}', value.get('apk_sha256', '')), 'INVALID_APK_DIGEST')
    require(value.get('source') in ('synthetic', 'android_lab'), 'INVALID_SOURCE')
    require(type(value.get('run_id')) is str and TOKEN.fullmatch(value['run_id']), 'INVALID_RUN_ID')
    require(type(value.get('repetition')) is int and value['repetition'] >= 0, 'INVALID_REPETITION')
    conditions = value.get('conditions', {})
    require(type(conditions) is dict and set(conditions) <= set(CONDITIONS), 'INVALID_CONDITIONS')
    for key, item in conditions.items():
        if item is None: continue
        if key in ('charging', 'power_save'): require(type(item) is bool, 'INVALID_CONDITION_TYPE')
        elif key == 'observer_lost_events': require(type(item) is int and item >= 0, 'INVALID_CONDITION_TYPE')
        elif key in ('android_api', 'page_bytes'): require(type(item) is int and item > 0, 'INVALID_CONDITION_TYPE')
        elif key == 'refresh_hz': require(finite(item, 1) and item <= 360, 'INVALID_CONDITION_TYPE')
        elif key == 'animation_scales': require(type(item) is list and len(item) == 3 and all(finite(x) and x <= 10 for x in item), 'INVALID_CONDITION_TYPE')
        elif key == 'resolution': require(type(item) is str and re.fullmatch(r'[1-9][0-9]{1,4}x[1-9][0-9]{1,4}', item), 'INVALID_CONDITION_TYPE')
        else: require(type(item) is str and TOKEN.fullmatch(item), 'INVALID_CONDITION_TYPE')
    return value


def report(meta, package, pids, log_text=None, frame_text=None, event_text=None,
           stream=None, log_window=None, frame_window=None):
    meta = metadata(meta)
    hashes = {name: hashlib.sha256(text.encode()).hexdigest() for name, text in
              [('logcat', log_text), ('gfxinfo', frame_text), ('events', event_text)] if text is not None}
    hz = meta.get('conditions', {}).get('refresh_hz')
    require(frame_text is None or hz is not None, 'REFRESH_RATE_REQUIRED_FOR_FRAMES')
    return {'schema': 1, 'metadata': meta, 'input_sha256': hashes,
            'logcat': logs(log_text, package, pids, log_window) if log_text is not None else None,
            'frames': frames(frame_text, hz, stream, frame_window) if frame_text is not None else None,
            'interactions': interactions(event_text) if event_text is not None else None,
            'android_execution_verified_by_analyzer': False}


def compare(baseline, candidate, min_runs=5):
    require(type(min_runs) is int and min_runs >= 5, 'FIVE_RUNS_MINIMUM')
    reasons = []
    all_runs = baseline + candidate
    if not all_runs: return {'status': 'INCOMPARABLE', 'reasons': ['NO_RUNS'], 'metrics': {}}
    for r in all_runs: metadata(r['metadata'])
    reference = all_runs[0]['metadata'].get('conditions', {})
    for key in CONDITIONS:
        if reference.get(key) is None or reference.get(key) == 'unknown' or any(r['metadata'].get('conditions', {}).get(key) != reference.get(key) for r in all_runs):
            reasons.append('CONDITION_' + key)
    if any(r['metadata'].get('conditions', {}).get('observer_lost_events') != 0 for r in all_runs):
        reasons.append('OBSERVER_LOST_EVENTS')
    for group in (baseline, candidate):
        if len(group) < min_runs: reasons.append('INSUFFICIENT_RUNS')
        identities = {(r['metadata']['client'], r['metadata']['apk_sha256']) for r in group}
        if len(identities) != 1: reasons.append('MIXED_BUILD_GROUP')
    run_ids = [r['metadata']['run_id'] for r in all_runs]
    if len(run_ids) != len(set(run_ids)): reasons.append('REUSED_RUN_ID')
    left = {r['metadata']['repetition']: r for r in baseline}
    right = {r['metadata']['repetition']: r for r in candidate}
    if len(left) != len(baseline) or len(right) != len(candidate) or set(left) != set(right): reasons.append('UNPAIRED_REPETITIONS')
    if len({r['metadata']['source'] for r in all_runs}) != 1: reasons.append('MIXED_SOURCES')
    if reasons: return {'status': 'INCOMPARABLE', 'reasons': sorted(set(reasons)), 'metrics': {}}
    outcomes = {}
    for op in OPS:
        pairs = []
        for repetition in sorted(left):
            rows = []
            for r in (left[repetition], right[repetition]):
                interaction = r.get('interactions') or {}
                row = interaction.get('operations', {}).get(op, {})
                metric = row.get('request_to_cancel' if op == 'transition_interrupt' else 'request_to_present', {})
                requested = row.get('requested')
                if (type(requested) is not int or requested < 10 or row.get('incomplete', 0)
                        or row.get('timeout', 0) or type(metric.get('n')) is not int
                        or metric['n'] != requested): break
                if op != 'transition_interrupt' and (row.get('cancelled', 0) or row.get('presented') != requested): break
                if rows and requested != left[repetition]['interactions']['operations'][op]['requested']: break
                rows.append(metric.get('p95_ms'))
            if len(rows) != 2 or not all(finite(x) for x in rows): break
            pairs.append(rows)
        if len(pairs) != len(left):
            outcomes[op] = {'status': 'INSUFFICIENT_OBSERVATIONS'}
            continue
        diffs = [b - a for a, b in pairs]
        outcomes[op] = {'status': 'CONSISTENT_OBSERVED_SLOWDOWN' if all(b - a > max(5, a * .10) for a, b in pairs) else 'NO_CONSISTENT_SLOWDOWN_AT_THRESHOLD',
                        'paired_runs': len(pairs), 'median_p95_delta_ms': statistics.median(diffs),
                        'baseline_median_p95_ms': statistics.median(a for a, b in pairs),
                        'candidate_median_p95_ms': statistics.median(b for a, b in pairs)}
    for field, floor in [('p95_ms', 2), ('over_budget_pct', 5)]:
        pairs = []
        for repetition in sorted(left):
            values = []
            for r in (left[repetition], right[repetition]):
                frame = r.get('frames') or {}
                metric = frame.get('metrics') or {}
                if (frame.get('status') != 'FRAME_SAMPLE' or frame.get('window_scoped') is not True
                        or type(metric.get('n')) is not int or metric['n'] < 30
                        or metric.get('invalid_rows', 0) or not finite(metric.get(field))): break
                values.append(metric[field])
            if len(values) != 2: break
            pairs.append(values)
        outcomes['frame_' + field] = (
            {'status': 'CONSISTENT_OBSERVED_SLOWDOWN' if all(b - a > (max(floor, a * .10) if field == 'p95_ms' else floor) for a, b in pairs) else 'NO_CONSISTENT_SLOWDOWN_AT_THRESHOLD',
             'paired_runs': len(pairs), 'median_delta': statistics.median(b - a for a, b in pairs)}
            if len(pairs) == len(left) else {'status': 'INSUFFICIENT_SCOPED_FRAMES'})
    observed = any(row['status'] in ('CONSISTENT_OBSERVED_SLOWDOWN', 'NO_CONSISTENT_SLOWDOWN_AT_THRESHOLD') for row in outcomes.values())
    return {'status': ('SYNTHETIC_COMPARISON_ONLY' if all_runs[0]['metadata']['source'] == 'synthetic' else 'OBSERVATIONAL_COMPARISON') if observed else 'INSUFFICIENT_OBSERVATIONS',
            'reasons': [] if observed else ['NO_COMPARABLE_METRIC'], 'metrics': outcomes,
            'limits': 'Paired observations, not causal attribution or statistical significance; >10% and >5ms in every pair. No winner declared.'}


def main():
    parser = SafeParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    one = sub.add_parser('analyze')
    one.add_argument('--metadata', type=Path, required=True)
    one.add_argument('--package', required=True)
    one.add_argument('--pids', type=int, nargs='*', default=[])
    for name in ('logcat', 'gfxinfo', 'events'): one.add_argument('--' + name, type=Path)
    one.add_argument('--stream', type=int)
    one.add_argument('--log-window', type=float, nargs=2)
    one.add_argument('--frame-window', type=int, nargs=2)
    two = sub.add_parser('compare')
    two.add_argument('--baseline', type=Path, nargs='+', required=True)
    two.add_argument('--candidate', type=Path, nargs='+', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'analyze':
            out = report(strict_json(read(args.metadata)), args.package, args.pids,
                         *[read(getattr(args, n)) if getattr(args, n) else None for n in ('logcat', 'gfxinfo', 'events')],
                         stream=args.stream, log_window=args.log_window, frame_window=args.frame_window)
        else:
            out = compare([strict_json(read(p)) for p in args.baseline], [strict_json(read(p)) for p in args.candidate])
        print(json.dumps(out, indent=2, sort_keys=True, allow_nan=False))
        return 2 if out.get('status') in ('INCOMPARABLE', 'INSUFFICIENT_OBSERVATIONS') else 0
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(json.dumps({'status': 'INVALID_INPUT', 'code': error.args[0] if isinstance(error, InputError) else 'INPUT_FORMAT_OR_IO', 'metrics': None}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
