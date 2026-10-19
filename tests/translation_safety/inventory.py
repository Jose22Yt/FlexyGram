"""Deterministic lexical source inventory, not an Android call-graph proof."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'TMessagesProj/src'
SNAPSHOT = Path(__file__).with_name('callsites.json')
STRINGS_COMMENTS = re.compile(
    r'"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')
CALLS = re.compile(
    r'\b(?:Translator(?:\.Companion)?\s*\.\s*(?:translate|translateArticle|translatePoll|translateWithContext)'
    r'|(?:GoogleAppTranslator|GoogleTranslator|GoogleCloudTranslator)\s*\.\s*doTranslate'
    r'|GoogleTranslatorNeko\s*\.\s*translate|GoogleAppTranslator\s*\.\s*getInstance'
    r'|translator\s*\.\s*(?:doTranslate|translate)'
    r'|(?:NekoMicrosoftTranslator|DeepLTranslator)\s*\.\s*getInstance'
    r'|(?:getBulkTranslateProvider|translateBase))\s*\(')


def collect():
    rows = []
    for path in sorted(SRC.rglob('*')):
        if path.suffix not in ('.kt', '.java'):
            continue
        text = path.read_text()
        clean = STRINGS_COMMENTS.sub(
            lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text)
        for match in CALLS.finditer(clean):
            if re.search(r'\bfun\s+$', clean[max(0, match.start()-30):match.start()]):
                continue
            symbol = re.sub(r'\s+', '', match[0]).removesuffix('(')
            rows.append({'path':str(path.relative_to(ROOT)),
                         'line':clean.count('\n', 0, match.start())+1,
                         'symbol':symbol})
    paths = sorted({row['path'] for row in rows})
    return {'schema':1, 'audited_source_base':'333dd8c9beb35a2e3caa985279858df7b5bc2ee7',
            'callsites':rows,
            'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
            'limits':'Lexical Kotlin/Java snapshot; reflection, generated code, plugins and binary calls need separate review.'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Explicit review step; never run automatically in tests')
    args = parser.parse_args()
    actual = collect()
    if args.write:
        SNAPSHOT.write_text(json.dumps(actual, indent=2)+'\n')
    else:
        assert actual == json.loads(SNAPSHOT.read_text()), 'Translation source/callsites changed; review required'
    print(json.dumps({'callsites':len(actual['callsites']),
                      'source_files':len(actual['source_sha256']), 'matches_reviewed_snapshot':True}))
