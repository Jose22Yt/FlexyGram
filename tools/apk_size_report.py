#!/usr/bin/env python3
"""Report compressed APK contributions without extracting or changing its content."""
import json
import sys
import zipfile
from pathlib import Path


def report(path):
    totals = {}
    with zipfile.ZipFile(path) as apk:
        for entry in apk.infolist():
            if entry.is_dir():
                continue
            name = entry.filename
            group = ('native' if name.startswith('lib/') else 'dex' if name.endswith('.dex')
                     else 'python' if 'chaquopy' in name else 'resources' if name.startswith('res/')
                     or name == 'resources.arsc' else 'other')
            bucket = totals.setdefault(group, {'compressed': 0, 'uncompressed': 0})
            bucket['compressed'] += entry.compress_size
            bucket['uncompressed'] += entry.file_size
    return {'apk': Path(path).name, 'bytes': Path(path).stat().st_size, 'groups': totals}


if __name__ == '__main__':
    print(json.dumps(report(sys.argv[1]), sort_keys=True))
