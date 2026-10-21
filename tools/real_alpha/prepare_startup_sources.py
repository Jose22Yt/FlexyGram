"""Exact-source diagnostic instrumentation. Does not edit shared/flavor sources or loosen build gates."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def generate(output):
    config=json.loads((ROOT/'tools/real_alpha/startup-overlays.json').read_text())
    receipt=[]
    for row in config['files']:
        source=ROOT/row['source'];raw=source.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['source_sha256']:raise ValueError('Startup baseline changed: review overlay '+row['source'])
        lines=raw.decode('utf-8').splitlines(keepends=True)
        previous=len(lines)+1
        for hunk in reversed(row['hunks']):
            if not 0<=hunk['start']<=hunk['end']<previous:raise ValueError('Invalid diagnostic hunk')
            lines[hunk['start']:hunk['end']]=hunk['replacement'];previous=hunk['start']+1
        instrumented=''.join(lines).encode()
        if hashlib.sha256(instrumented).hexdigest()!=row['output_sha256']:raise ValueError('Instrumented source mismatch')
        target=output/row['source'].split('/java/',1)[1]
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(instrumented)
        receipt.append({k:row[k] for k in ('source','source_sha256','output_sha256')})
    output.mkdir(parents=True,exist_ok=True)
    (output/'startup-overlay-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    print(json.dumps(generate(p.parse_args().output)))
