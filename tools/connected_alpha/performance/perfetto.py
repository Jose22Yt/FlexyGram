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
  atrace_categories: "input"
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
    frame_quantiles = f'''-- Nearest-rank quantiles of app SURFACE durations, not display FPS or input latency.
WITH frames AS (
 SELECT a.dur/1e6 AS ms FROM actual_frame_timeline_slice a JOIN process p USING(upid)
 WHERE (p.name = '{package}' OR p.name GLOB '{package}:*') AND a.dur >= 0
), ranked AS (SELECT ms,ROW_NUMBER() OVER(ORDER BY ms) AS rn,COUNT(*) OVER() AS n FROM frames)
SELECT COUNT(*) AS surface_records,
 MIN(CASE WHEN rn >= (n*50+99)/100 THEN ms END) AS p50_ms,
 MIN(CASE WHEN rn >= (n*95+99)/100 THEN ms END) AS p95_ms,
 MIN(CASE WHEN rn >= (n*99+99)/100 THEN ms END) AS p99_ms FROM ranked;
'''
    blur = f'''-- Explicit local markers, no wallpaper/chat/user identifiers.
SELECT s.name,COUNT(*) AS events,SUM(s.dur)/1e6 AS total_ms,MAX(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t USING(utid) JOIN process p USING(upid)
WHERE (p.name = '{package}' OR p.name GLOB '{package}:*') AND s.name GLOB 'Flexy.blur.*' AND s.dur>=0 GROUP BY s.name;
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
    phases = f"""-- Phase completion is NOT visible rows, useful connection or interactive readiness.
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
 SELECT startup_id,startup_type,ts,LEAD(ts) OVER(ORDER BY ts) AS next_ts
 FROM android_startups WHERE package = '{package}'
)
SELECT s.startup_id,s.startup_type,ph.name AS phase,
 (ph.ts-s.ts)/1e6 AS phase_start_ms,(ph.ts+ph.dur-s.ts)/1e6 AS phase_complete_ms,
 ph.dur/1e6 AS phase_duration_ms
FROM starts s JOIN slice ph ON ph.ts>=s.ts AND (s.next_ts IS NULL OR ph.ts<s.next_ts)
 JOIN thread_track tt ON tt.id=ph.track_id JOIN thread th ON th.utid=tt.utid
 JOIN process p ON p.upid=th.upid
WHERE (p.name='{package}' OR p.name GLOB '{package}:*') AND ph.dur>=0
 AND ph.name IN ('Flexy.startup.post_init','Flexy.startup.request_local_dialogs',
 'Flexy.dialogs.read_local','Flexy.startup.account_services')
ORDER BY s.startup_id,ph.ts;
"""
    return {'config': config, 'frame_sql': sql, 'frame_quantiles_sql': frame_quantiles, 'blur_sql': blur, 'cpu_sql': cpu, 'startup_sql': startup, 'startup_phases_sql': phases,
            'limits': {'touch_latency': 'NOT_IMPLEMENTED_WITHOUT_INPUT_TO_PRESENT_FLOW',
                       'gpu_utilization': 'REQUIRES_SUPPORTED_DEVICE_GPU_COUNTERS',
                       'allocation_counts': 'REQUIRES_SEPARATE_HEAPPROFD_OR_ART_CAPTURE',
                       'local_rows_visible': 'NOT_INFERRED_FROM_SQLITE_OR_ENQUEUE_COMPLETION',
                       'useful_connection': 'REQUIRES_SUCCESSFUL_NETWORK_RESPONSE_TIMING',
                       'new_updates': 'REQUIRES_SERVER_UPDATE_TIMING',
                       'chat_load': 'REQUIRES_MATCHED_CHAT_INPUT_TO_PRESENT_CAPTURE',
                       'account': 'PREPARED_TEST_DEVICE_ONLY', 'buffer_mib': 32, 'seconds': seconds}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', required=True)
    p.add_argument('--seconds', type=int, default=20)
    p.add_argument('--out-dir', type=Path, required=True)
    a = p.parse_args()
    result = plan(a.package, a.seconds)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for key, name in [('config', 'test_trace.pbtxt'), ('frame_sql', 'frame_timeline.sql'), ('frame_quantiles_sql', 'frame_quantiles.sql'), ('blur_sql', 'instant_blur.sql'), ('cpu_sql', 'scheduled_cpu.sql'), ('startup_sql', 'startup.sql'), ('startup_phases_sql', 'startup_phases.sql')]:
        (a.out_dir / name).write_text(result[key])
    (a.out_dir / 'limits.json').write_text(json.dumps(result['limits'], indent=2) + '\n')

if __name__ == '__main__':
    main()
