#!/usr/bin/env python3
"""Generate bounded local TEST-device trace/query plans; do not capture or upload a trace."""
import argparse
import json
from pathlib import Path
import re


def plan(package, seconds=20):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+', package) or not 1 <= seconds <= 60:
        raise ValueError('Valid package and bounded1–60second test trace required')
    config = '''buffers { size_kb: 32768 fill_policy: RING_BUFFER }
duration_ms: _DURATION_
data_sources { config { name: "android.surfaceflinger.frametimeline" } }
data_sources { config { name: "linux.process_stats" process_stats_config { scan_all_processes_on_start: true } } }
data_sources { config { name: "linux.ftrace" ftrace_config {
  ftrace_events: "sched/sched_switch"
  ftrace_events: "sched/sched_waking"
  atrace_categories: "gfx"
  atrace_categories: "view"
  atrace_categories: "wm"
  atrace_categories: "am"
  atrace_categories: "dalvik"
  atrace_apps: "_PACKAGE_"
} } }
'''.replace('_DURATION_', str(seconds * 1000)).replace('_PACKAGE_', package)
    sql = f'''-- Official FrameTimeline tables. App surface frames, not touch latency/display refresh counts.
WITH app_frames AS (
 SELECT a.* FROM actual_frame_timeline_slice a JOIN process p USING(upid)
 WHERE (p.name = '{package}' OR p.name GLOB '{package}:*') AND a.dur >= 0
)
SELECT COUNT(*) AS app_surface_frame_records,
 SUM(CASE WHEN jank_type = 'None' THEN 1 ELSE 0 END) AS no_jank_records,
 SUM(CASE WHEN jank_type IS NULL OR jank_type IN ('Unknown','Unspecified','') THEN 1 ELSE 0 END) AS unclassified_records,
 SUM(CASE WHEN jank_type IS NOT NULL AND jank_type NOT IN ('None','Unknown','Unspecified','') THEN 1 ELSE 0 END) AS classified_jank_records,
 SUM(CASE WHEN on_time_finish = 0 THEN 1 ELSE 0 END) AS late_finish_records,
 MIN(dur)/1e6 AS min_surface_frame_ms, MAX(dur)/1e6 AS max_surface_frame_ms
FROM app_frames;
'''
    cpu = f'''-- Scheduled CPU duration only, not wall time/RenderThread GPU utilization.
SELECT CASE WHEN t.tid = p.pid THEN 'main' WHEN t.name = 'RenderThread' THEN 'render' ELSE 'other' END AS thread_role,
 COUNT(*) AS scheduled_slices, SUM(s.dur)/1e6 AS scheduled_cpu_ms
FROM sched s JOIN thread t USING(utid) JOIN process p USING(upid)
WHERE (p.name = '{package}' OR p.name GLOB '{package}:*') AND s.dur > 0
GROUP BY thread_role;
'''
    startup = f"""INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_type, s.dur/1e6 AS startup_duration_ms,
 t.time_to_initial_display/1e6 AS time_to_initial_display_ms,
 t.time_to_full_display/1e6 AS time_to_full_display_ms
FROM android_startups s LEFT JOIN android_startup_time_to_display t USING(startup_id)
WHERE s.package = '{package}';
"""
    return {'config': config, 'frame_sql': sql, 'cpu_sql': cpu, 'startup_sql': startup,
            'limits': {'touch_latency': 'NOT_IMPLEMENTED_WITHOUT_INPUT_TO_PRESENT_FLOW',
                       'gpu_utilization': 'REQUIRES_SUPPORTED_DEVICE_GPU_COUNTERS',
                       'allocation_counts': 'REQUIRES_SEPARATE_HEAPPROFD_OR_ART_CAPTURE',
                       'account': 'PREPARED_TEST_DEVICE_ONLY', 'buffer_mib': 32, 'seconds': seconds}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', required=True)
    p.add_argument('--seconds', type=int, default=20)
    p.add_argument('--out-dir', type=Path, required=True)
    a = p.parse_args()
    result = plan(a.package, a.seconds)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for key, name in [('config', 'test_trace.pbtxt'), ('frame_sql', 'frame_timeline.sql'), ('cpu_sql', 'scheduled_cpu.sql'), ('startup_sql', 'startup.sql')]:
        (a.out_dir / name).write_text(result[key])
    (a.out_dir / 'limits.json').write_text(json.dumps(result['limits'], indent=2) + '\n')

if __name__ == '__main__':
    main()
