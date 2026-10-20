"""Independent beta-diagnostics gate. Does not modify/run the historical 367 gate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
MINIMUM=85


def snapshot():
    paths=list((ROOT/'tools/beta_diagnostics').glob('*.py'))+list(Path(__file__).parent.glob('*.py'))
    paths.append(ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/NotificationCenter.java')
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def flatten(suite):
    return [name for item in suite for name in (flatten(item) if isinstance(item,unittest.TestSuite) else [item.id()])]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if sys.version_info[:2]!=(3,11):raise SystemExit('Python 3.11 required')
    before=snapshot()
    directory=str(Path(__file__).resolve().parent)
    suite=unittest.TestLoader().discover(directory,top_level_dir=directory)
    names=flatten(suite)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    row=dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
             skipped=len(result.skipped),expected_failures=len(result.expectedFailures),unexpected_successes=len(result.unexpectedSuccesses))
    passed=row['tests_run']-sum(row[k] for k in ('failures','errors','skipped','expected_failures','unexpected_successes'))
    complete=(result.testsRun>=MINIMUM and len(names)==len(set(names))==result.testsRun and before==snapshot())
    row.update(status='PASS' if result.wasSuccessful() and complete and not result.skipped and not result.expectedFailures else 'BLOCKED',
               passed=passed,distinct_tests=len(set(names)),minimum_required=MINIMUM,
               python=sys.version.split()[0],optimized=bool(sys.flags.optimize),source_sha256=before,
               test_ids=names,android_executed=False,apk_built=False,
               limits='Synthetic Python plus extracted real Java method with clock/queue doubles; no Android performance result')
    payload=json.dumps(row,indent=2,sort_keys=True)+'\n'
    if args.output:args.output.write_text(payload,encoding='utf-8')
    print(payload,end='')
    return 0 if row['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
