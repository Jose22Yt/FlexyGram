"""Deterministic offline wheel overlay. Does not modify the approved wheel lock.
Wheel contents and metadata remain byte-for-byte original except four source-built
ELF files, explicit Build tag, WHEEL provenance and freshly calculated RECORD.
No secret or APK is published by this tool.
"""
from pathlib import Path
from io import BytesIO,StringIO
import argparse,base64,csv,hashlib,json,zipfile
from audit import elf
from acceptance import candidate_contract
from wheelhouse import verified,select

def sha(data):return hashlib.sha256(data).hexdigest()
def record(files):
 stream=StringIO(newline='');writer=csv.writer(stream,lineterminator='\n')
 for name,data in sorted(files.items()):
  writer.writerow([name,'',''] if name.endswith('.dist-info/RECORD') else
   [name,'sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode(),str(len(data))])
 return stream.getvalue().encode()
def repack(original,replacements):
 with zipfile.ZipFile(BytesIO(original)) as z:
  if z.testzip() is not None:raise ValueError('Original wheel CRC')
  if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate original ZIP path')
  files={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
 for name,data in replacements.items():
  if name not in files:raise ValueError('Replacement not in original wheel')
  c=candidate_contract(elf(files[name],name),elf(data,name))
  if not c['static_contract_pass']:raise ValueError('Replacement ABI blocked: '+str(c))
  files[name]=data
 metadata=[n for n in files if n.endswith('.dist-info/WHEEL')]
 if len(metadata)!=1:raise ValueError('Expected one WHEEL')
 text=files[metadata[0]].decode().replace('android_21_arm64_v8a','android_24_arm64_v8a');lines=[x for x in text.splitlines() if not x.startswith(('Build:','Generator:'))]
 files[metadata[0]]=('\n'.join(lines)+'\nBuild: 3flexygram16k\nGenerator: FlexyGram isolated source-rebuild experiment\n').encode()
 records=[n for n in files if n.endswith('.dist-info/RECORD')]
 if len(records)!=1:raise ValueError('Expected one RECORD')
 files[records[0]]=record(files)
 result=BytesIO()
 with zipfile.ZipFile(result,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in sorted(files.items()):
   info=zipfile.ZipInfo(name,date_time=(2018,4,19,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
   info.create_system=3;info.external_attr=0o100644<<16;z.writestr(info,data,compresslevel=9)
 return result.getvalue()
def verify(manifest,dest):
 if dest.is_symlink() or not dest.is_dir():raise ValueError('Unsafe wheelhouse root')
 rows=manifest['wheels'];expected={r['filename'] for r in rows}
 if set(p.name for p in dest.iterdir())!=expected:raise ValueError('Experimental wheelhouse inventory mismatch')
 for row in rows:
  if not verified(dest/row['filename'],row):raise ValueError('Missing/non-file experimental wheel')
 return len(rows)
def prepare(original_dir,candidate_dir,dest,lock,source_manifest):
 if dest.is_symlink() or (dest.exists() and any(dest.iterdir())):raise ValueError('Use empty isolated wheelhouse')
 dest.mkdir(parents=True,exist_ok=True);source={r['filename']:r for r in source_manifest['original_wheels']};rows=[]
 for row in select(lock,['arm64-v8a']):
  original=original_dir/row['filename']
  if not verified(original,row):raise ValueError('Original input missing')
  data=original.read_bytes();filename=row['filename'];new=filename in source
  if new:
   replacements={}
   for name in source[filename]['libraries']:
    path=candidate_dir/('freetype-build' if name=='libfreetype.so' else 'prefix/lib')/name
    replacements['chaquopy/lib/'+name]=path.read_bytes()
   data=repack(data,replacements);filename=filename.replace('-2-py3-','-3flexygram16k-py3-').replace('android_21_arm64_v8a','android_24_arm64_v8a')
   if filename==row['filename']:raise ValueError('Expected original build tag 2')
  (dest/filename).write_bytes(data)
  rows.append({'filename':filename,'sha256':sha(data),'original_filename':row['filename'],
   'original_sha256':row['sha256'],'original_url':row['url'],'rebuilt':new})
 manifest={'schema':1,'experimental_only':True,'abi':'arm64-v8a','wheels':rows,
  'source_manifest_sha256':sha(json.dumps(source_manifest,sort_keys=True,separators=(',',':')).encode()),
  'android_runtime_validated':False}
 verify(manifest,dest);return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
 v=sub.add_parser('verify');v.add_argument('--manifest',type=Path,required=True);v.add_argument('--wheelhouse',type=Path,required=True)
 a=p.parse_args();print('Verified experimental wheels:',verify(json.loads(a.manifest.read_text()),a.wheelhouse))
