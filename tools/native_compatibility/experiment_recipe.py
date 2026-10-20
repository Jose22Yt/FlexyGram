"""Reproducible isolated 16 KB wheel experiment; no active dependency changes.
Runs offline from hash-pinned source archives + the original verified wheelhouse.
Build GNU ld separately with --build-linker; then --finalize two independent
rebuild_candidates.py outputs. Android execution remains a separate requirement.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,tarfile,zipfile
from rebuild_candidates import verify_archive
from compat_relink import relink
from experimental_wheels import prepare
BINUTILS={'file':'binutils-2.42.tar.xz','url':'https://ftp.gnu.org/gnu/binutils/binutils-2.42.tar.xz',
 'sha256':'f6e4d41fd5fc778b06b7891457b3620da5ecea1006c6a4a41ae998109f85a800'}
GNU_FLAGS=['--target=aarch64-linux-android','--disable-nls','--disable-werror','--disable-gdb',
 '--disable-gdbserver','--disable-gprofng','--disable-gprof','--disable-gas','--disable-binutils',
 '--without-zstd','--disable-sim','--disable-ctf']

def build_linker(sources,output):
 verify_archive(sources/BINUTILS['file'],BINUTILS['sha256'])
 if output.exists() and any(output.iterdir()):raise ValueError('Use empty linker build directory')
 output.mkdir(parents=True,exist_ok=True);src=output/'sources';src.mkdir()
 with tarfile.open(sources/BINUTILS['file']) as t:t.extractall(src,filter='data')
 build=output/'build';build.mkdir();commands=[[str(src/'binutils-2.42/configure'),*GNU_FLAGS],['make','-j2','all-ld','MAKEINFO=true']]
 with (output/'build.log').open('w') as log:
  for args in commands:subprocess.run(args,cwd=build,stdout=log,stderr=subprocess.STDOUT,check=True)
 return {'source':BINUTILS,'commands':commands,'linker_sha256':hashlib.sha256((build/'ld/ld-new').read_bytes()).hexdigest(),
  'documentation_generation_only_disabled':True}

def original_libraries(wheelhouse,manifest):
 originals={}
 from wheelhouse import verified
 for row in manifest['original_wheels']:
  if not verified(wheelhouse/row['filename'],row):raise ValueError('Original wheel missing')
  with zipfile.ZipFile(wheelhouse/row['filename']) as z:
   for n in row['libraries']:originals[n]=z.read('chaquopy/lib/'+n)
 return originals

def restore_maps(sources,output,manifest):
 for row in manifest['archives']:
  if row['file'].startswith(('libxml2','libxslt')):
   archive=sources/row['file'];verify_archive(archive,row['sha256'])
   with tarfile.open(archive) as t:
    for member in t.getmembers():
     if member.name.endswith(('/libxml2.syms','/libxslt/libxslt.syms')):
      (output/'sources'/member.name).write_bytes(t.extractfile(member).read())

def plugin_default(original):
 paths=set(re.findall(rb'[ -~]+/libxslt-plugins',original))
 if len(paths)!=1:raise ValueError('Original plugin default path absent/ambiguous')
 return paths.pop().decode()

def finalize(sources,output,ndk,cmake,wheelhouse,linker,manifest,wheel_output=None):
 originals=original_libraries(wheelhouse,manifest);restore_maps(sources,output,manifest)
 # Preserve the exact original default, including its non-operational build-host
 # path, rather than changing plugin behavior or embedding our output directory.
 # Explicit callers/environment plugin paths and module support remain intact.
 header=output/'sources/libxslt-1.1.32/libxslt/xsltconfig.h';text=header.read_text()
 text,count=re.subn(r'(#define LIBXSLT_DEFAULT_PLUGINS_PATH\(\) )"[^"\n]+"',
  lambda m:m[1]+json.dumps(plugin_default(originals['libxslt.so'])),text)
 if count!=1:raise ValueError('Plugin default macro shape changed')
 header.write_text(text)
 with (output/'xslt.repro.log').open('w') as log:
  subprocess.run(['make','-j2','V=1'],cwd=output/'sources/libxslt-1.1.32',stdout=log,stderr=subprocess.STDOUT,check=True)
 # NDK27 stubs use zstd-compressed DWARF. GNU built without host zstd cannot read
 # them. Decompress debug sections in isolated COPIES, retaining all dynamic ABI.
 # Original NDK and the APK libraries are never modified by objcopy.
 stubs=output/'gnu-ndk-stubs';stubs.mkdir(exist_ok=True);tool=ndk/'toolchains/llvm/prebuilt/linux-x86_64'
 from abi_report import detail
 copies=[]
 for p in (tool/'sysroot/usr/lib/aarch64-linux-android/24').glob('*.so'):
  if p.read_bytes().startswith(b'\x7fELF'):
   target=stubs/p.name
   subprocess.run([str(tool/'bin/llvm-objcopy'),'--decompress-debug-sections',str(p),str(target)],check=True)
   if detail(p.read_bytes())!=detail(target.read_bytes()):raise ValueError('NDK stub dynamic ABI changed')
   copies.append({'name':p.name,'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
    'decompressed_sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
 rows=relink(output,ndk,originals,linker,stubs)
 from abi_report import compare
 for n in ['libfreetype.so','libxml2.so','libxslt.so','libexslt.so']:
  path=output/('freetype-build' if n=='libfreetype.so' else 'prefix/lib')/n
  report=compare(originals[n],path.read_bytes(),n)
  if not report['static_abi_pass']:raise ValueError('Typed ABI/GNU parent contract failed: '+str(report))
 (output/'compat-report.json').write_text(json.dumps({'libraries':rows,'ndk_stub_debug_copies':copies,
  'linker_sha256':hashlib.sha256(linker.read_bytes()).hexdigest(),'plugin_default_preserved':True},indent=2)+'\n')
 result=prepare(wheelhouse,output,wheel_output or output/'wheels',json.loads(Path(__file__).resolve().parents[2].joinpath('TMessagesProj/python/wheels.lock.json').read_text()),manifest)
 (output/'wheels-manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-linker',action='store_true');p.add_argument('--sources',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 for n in ['ndk','cmake','wheelhouse','linker']:p.add_argument('--'+n,type=Path)
 p.add_argument('--wheel-output',type=Path,help='New immutable wheel directory for a repeated finalization')
 a=p.parse_args()
 if a.build_linker:r=build_linker(a.sources.resolve(),a.output.resolve())
 else:
  if not all([a.ndk,a.cmake,a.wheelhouse,a.linker]):p.error('Finalize requires ndk/cmake/wheelhouse/linker')
  m=json.loads(Path(__file__).with_name('rebuild-sources.json').read_text())
  r=finalize(*(getattr(a,k).resolve() for k in ['sources','output','ndk','cmake','wheelhouse','linker']),m,wheel_output=a.wheel_output.resolve() if a.wheel_output else None)
 print(json.dumps({'success':True,'experimental_only':True,'android_runtime_validated':False}))
