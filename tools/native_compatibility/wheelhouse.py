"""Materialize public, hash-locked wheels. Never execute wheel contents or use pip indexes.
Build dependency downloads only; not application service configuration.
"""
from pathlib import Path
import argparse,hashlib,json,os,tempfile,urllib.request,zipfile

def select(lock,abis):
    if lock['schema'] != 1 or lock['python'] != '3.11':raise ValueError('Unsupported wheel lock')
    if not abis or set(abis)-set(lock['abis']):raise ValueError('Unsupported ABI')
    tags={'arm64-v8a':'arm64_v8a','x86_64':'x86_64'}
    return [f for p in lock['packages'] for f in p['files']
            if '-any.whl' in f['filename'] or any(f['filename'].endswith('_'+tags[a]+'.whl') for a in abis)]
def verified(path,row):
    if path.is_symlink():raise ValueError('Symlink is not allowed in locked wheelhouse: '+path.name)
    if not path.is_file():return False
    if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Wheel digest mismatch: '+row['filename'])
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:raise ValueError('Wheel CRC mismatch')
    return True

def prepare(lock,dest,abis,offline=False,cache=None):
    # Reject redirects of the entire directory, not only individual wheel files.
    if dest.is_symlink():raise ValueError('Wheelhouse destination cannot be a symlink')
    dest.mkdir(parents=True,exist_ok=True)
    cache=cache or Path.home()/'.cache/flexygram/wheels'
    if cache.is_symlink():raise ValueError('Wheelhouse cache cannot be a symlink')
    cache.mkdir(parents=True,exist_ok=True)
    selected=select(lock,abis)
    known={f['filename']:f for p in lock['packages'] for f in p['files']}
    # A previous supported ABI may remain; verify it too. Never admit an unlisted build tag.
    for existing in dest.iterdir():
        if existing.is_symlink() or not existing.is_file() or existing.name not in known:
            raise ValueError('Wheelhouse contains unlisted or unsafe entry; use an empty output directory')
        verified(existing,known[existing.name])
    for row in selected:
        name=row['filename'];url=row['url'];digest=row['sha256']
        if Path(name).name!=name or not name.endswith('.whl') or len(digest)!=64:raise ValueError('Malformed lock entry')
        if not (url.startswith('https://files.pythonhosted.org/') or url.startswith('https://chaquo.com/pypi-13.1/')):raise ValueError('Unapproved wheel origin')
        output=dest/name
        if verified(output,row):continue
        cached=cache/name
        if not verified(cached,row):
            if offline:raise ValueError('Missing locked wheel in offline cache: '+name)
            # A failed download cannot become a usable cache entry.
            with urllib.request.urlopen(url,timeout=90) as response:payload=response.read()
            if hashlib.sha256(payload).hexdigest()!=digest:raise ValueError('Downloaded wheel digest mismatch: '+name)
            with tempfile.NamedTemporaryFile(dir=cache,delete=False) as tmp:
                tmp.write(payload);temporary=Path(tmp.name)
            try:
                verified(temporary,row);os.replace(temporary,cached)
            finally:temporary.unlink(missing_ok=True)
        output.write_bytes(cached.read_bytes());verified(output,row)
    return len(selected)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lock',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--abi',action='append',required=True);p.add_argument('--offline',action='store_true');p.add_argument('--cache',type=Path)
    a=p.parse_args();print('Verified locked wheels:',prepare(json.loads(a.lock.read_text()),a.output,a.abi,a.offline,a.cache))
