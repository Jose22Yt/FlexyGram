"""Compare AndroidX Macrobenchmark JSON from two runs on the same device."""
import argparse
import json
import math
from pathlib import Path


METRICS = {
    "coldStartup": {"timeToInitialDisplayMs": "median", "timeToFullDisplayMs": "median"},
    "warmStartup": {"timeToInitialDisplayMs": "median", "timeToFullDisplayMs": "median"},
    "homeScroll": {"frameOverrunMs": "P95"},
    "messageScroll": {"frameOverrunMs": "P95"},
    "openChatToVisibleHistory": {"openChatToVisibleHistoryFirstMs": "median"},
}


def _identity(report):
    build = report["context"]["build"]
    return build["model"], build["fingerprint"], build["version"]["sdk"]


def _metric(report, name, metric, statistic):
    matching = [row for row in report["benchmarks"] if row["name"].split("[")[0] == name]
    if len(matching) != 1:
        raise ValueError(f"Expected exactly one measurement for {name}")
    row = matching[0]
    # AndroidX records per-iteration values in metrics and per-frame values in sampledMetrics.
    summary = row.get("metrics", {}).get(metric)
    if summary is None:
        summary = row.get("sampledMetrics", {}).get(metric)
    value = summary.get(statistic) if summary else None
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ValueError(f"{name} lacks a valid {metric}/{statistic} measurement")
    return value


def compare(baseline, candidate, journeys):
    if _identity(baseline) != _identity(candidate):
        raise ValueError("Capture both runs on the same device and Android build")
    rows = []
    for name in journeys:
        for metric, statistic in METRICS[name].items():
            before = _metric(baseline, name, metric, statistic)
            after = _metric(candidate, name, metric, statistic)
            rows.append((name, metric, statistic, before, after, after - before))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--journey", choices=METRICS, action="append")
    args = parser.parse_args()
    try:
        rows = compare(json.loads(args.baseline.read_text()), json.loads(args.candidate.read_text()),
                       args.journey or METRICS)
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    print("journey\tmetric\tstatistic\tbaseline_ms\tcandidate_ms\tdelta_ms")
    for name, metric, statistic, before, after, delta in rows:
        print(f"{name}\t{metric}\t{statistic}\t{before:.2f}\t{after:.2f}\t{delta:+.2f}")


if __name__ == "__main__":
    main()
