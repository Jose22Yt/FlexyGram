#!/usr/bin/env python3
"""Windowed numeric local trace analysis. Never captures inputs, automates UI or uploads traces."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import tempfile
from .metrics import summary
from .perfetto import plan


def queries(package, start, end):
    plan(package)  # reuse strict package validation
    if type(start) is not int or type(end) is not int or not 0 <= start < end or end - start > 60_000_000_000:
        raise ValueError('Explicit trace-clock window of at most60 seconds required')
    app = f"(p.name = '{package}' OR p.name GLOB '{package}:*')"
    overlap = f'MIN(s.ts+s.dur,{end})-MAX(s.ts,{start})'
    return {
        'cpu': f'''SELECT CASE WHEN t.tid=p.pid THEN 0 WHEN t.name='RenderThread' THEN 1 ELSE 2 END AS role,
 SUM({overlap})/1e6 AS scheduled_cpu_ms
 FROM sched s JOIN thread t USING(utid) JOIN process p USING(upid)
 WHERE {app} AND s.dur>0 AND s.ts<{end} AND s.ts+s.dur>{start} GROUP BY role;''',
        'main_state': f'''SELECT SUM({overlap})/1e6 AS runnable_ms
 FROM thread_state s JOIN thread t USING(utid) JOIN process p USING(upid)
 WHERE {app} AND t.tid=p.pid AND s.state IN ('R','R+') AND s.dur>0
 AND s.ts<{end} AND s.ts+s.dur>{start};''',
        'frames': f'''SELECT a.dur/1e6 AS surface_frame_ms,
 CASE WHEN a.jank_type='None' THEN 0
 WHEN a.jank_type IS NULL OR a.jank_type IN ('Unknown','Unspecified','') THEN NULL ELSE 1 END AS jank
 FROM actual_frame_timeline_slice a JOIN process p USING(upid)
 WHERE {app} AND a.dur>=0 AND a.ts>={start} AND a.ts+a.dur<={end};''',
        'input': f'''INCLUDE PERFETTO MODULE android.input;
 SELECT dispatch_latency_dur/1e6 AS dispatch_ms, handling_latency_dur/1e6 AS handling_ms,
 total_latency_dur/1e6 AS dispatch_to_ack_ms,
 CASE WHEN frame_id IS NOT NULL AND is_speculative_frame=0 AND end_to_end_latency_dur>=0
 AND read_time+end_to_end_latency_dur<={end} THEN end_to_end_latency_dur/1e6 ELSE NULL END AS input_read_to_present_ms
 FROM android_input_events WHERE (process_name='{package}' OR process_name GLOB '{package}:*')
 AND read_time>={start} AND read_time<{end};''',
        'gc': f'''INCLUDE PERFETTO MODULE android.garbage_collection;
 SELECT gc_dur/1e6 AS collection_wall_ms, reclaimed_mb FROM android_garbage_collection_events
 WHERE (process_name='{package}' OR process_name GLOB '{package}:*')
 AND gc_dur>=0 AND gc_ts>={start} AND gc_ts+gc_dur<={end};''',
    }


def csv_numbers(text):
    rows = []
    reader = csv.DictReader(io.StringIO(text.strip()))
    for row in reader:
        parsed = {}
        for key, value in row.items():
            if key is None or value is None:
                raise ValueError('Truncated trace CSV')
            if value.strip().upper() in ('', 'NULL', '[NULL]'):
                parsed[key] = None
                continue
            number = float(value)
            if not math.isfinite(number) or number < 0:
                raise ValueError('Invalid numeric trace result')
            parsed[key] = number
        rows.append(parsed)
    return rows


def summarize(tables):
    def values(table, column):
        return [row[column] for row in tables.get(table, []) if row.get(column) is not None]
    frames = tables.get('frames', [])
    inputs = tables.get('input', [])
    return {'surface_frame_ms': summary(values('frames','surface_frame_ms')),
            'classified_jank_records': sum(r.get('jank') == 1 for r in frames),
            'unclassified_frame_records': sum(r.get('jank') is None for r in frames),
            'surface_record_count': len(frames),
            'input_read_to_present_ms': summary(values('input','input_read_to_present_ms')),
            'input_events_without_exact_present': sum(r.get('input_read_to_present_ms') is None for r in inputs),
            'dispatch_to_ack_ms': summary(values('input','dispatch_to_ack_ms')),
            'handling_ms': summary(values('input','handling_ms')),
            'scheduled_cpu_by_role': tables.get('cpu'), 'main_runnable': tables.get('main_state'),
            'gc_event_wall_ms': summary(values('gc','collection_wall_ms')),
            'gc_reclaimed_mb': summary(values('gc','reclaimed_mb')),
            'first_useful_chat_frame_ms': None, 'first_interaction_possible_ms': None,
            'gpu_utilization': None,
            'limits': 'Exact input association is OS input-read to present, not semantic chat readiness, touch hardware latency or ACK latency. Missing data remains unknown; zero GC rows does not prove zero GC.'}


def analyze(binary, trace, package, start, end, execute=subprocess.run):
    tables = {}
    unavailable = []
    help_result = execute([str(binary),'query','--help'],capture_output=True,text=True,timeout=10)
    # v58.2 emits CSV by default; newer versions expose --format and may auto-enable agent mode.
    formatting = ['--format','csv'] if '--format' in help_result.stdout + help_result.stderr else []
    with tempfile.TemporaryDirectory(prefix='flexygram-local-queries-') as temp:
        for name, sql in queries(package,start,end).items():
            path = Path(temp)/(name+'.sql');path.write_text(sql)
            # Current official native CLI. Explicit local executable; no downloader/server/network.
            result = execute([str(binary),'query',*formatting,'-f',str(path),str(trace)],
                             capture_output=True,text=True,timeout=120)
            if result.returncode:
                unavailable.append(name)  # Do not echo raw trace/error strings into reports.
            else:
                tables[name] = csv_numbers(result.stdout)
    return {'schema':2,'evidence':'local_trace_numeric_extract',
            'window_ns':{'start':start,'end':end},'available_queries':sorted(tables),
            'unavailable_queries':unavailable,'metrics':summarize(tables),'superiority':'NOT_ESTABLISHED'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trace-processor',required=True,type=Path,help='Local native Perfetto binary with query subcommand; no download wrapper')
    p.add_argument('--trace',required=True,type=Path)
    p.add_argument('--package',required=True)
    p.add_argument('--start-ns',required=True,type=int);p.add_argument('--end-ns',required=True,type=int)
    p.add_argument('--confirm-test-trace',action='store_true',required=True)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    if not a.trace_processor.is_file() or not a.trace.is_file():p.error('Existing local binary and prepared-test trace required')
    # Fingerprint without preserving any raw trace content/path in the numerical report.
    digest=hashlib.sha256()
    with a.trace.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    result=analyze(a.trace_processor.resolve(),a.trace.resolve(),a.package,a.start_ns,a.end_ns)
    result['trace_sha256']=digest.hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return 0 if not result['unavailable_queries'] else 2

if __name__=='__main__':raise SystemExit(main())
