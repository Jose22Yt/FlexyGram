"""Four tiny synthetic ARM64 ELF fixtures; no application rebuild or execution."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tests/native_compatibility'))
from elf_candidate_review import inspect,compare,require

def experiment(ndk,work):
 require('Pkg.Revision = 27.2.12479018' in (ndk/'source.properties').read_text(),'Pinned NDK27.2 required')
 require(not work.exists() and work.parent.is_dir() and ROOT not in work.resolve().parents and not any(p.is_symlink() for p in work.parents),'New private fixture directory required')
 a=work/'short';b=work/('long_'+'x'*150);a.mkdir(parents=True);b.mkdir()
 source='const char *lab_origin(void){return __FILE__;}\nunsigned lab_origin_size(void){return sizeof(__FILE__);}\n'
 tools=ndk/'toolchains/llvm/prebuilt/linux-x86_64/bin';results={}
 for normalized in [False,True]:
  rows=[]
  for directory in [a,b]:
   path=directory/'probe.c';path.write_text(source);out=directory/('normalized.so'if normalized else'plain.so')
   flags=['-ffile-prefix-map='+str(directory)+'=/flexygram-lab/canonical']if normalized else[]
   subprocess.run([str(tools/'aarch64-linux-android24-clang'),'-shared','-fPIC','-O2','-g','-Wl,-soname,liblab_synthetic.so','-Wl,-z,max-page-size=16384',*flags,str(path),'-o',str(out)],check=True,capture_output=True)
   subprocess.run([str(tools/'llvm-strip'),'--strip-unneeded',str(out)],check=True,capture_output=True)
   rows.append(inspect(out.read_bytes()))
  result=compare(*rows);result['left_sha256']=rows[0]['sha256'];result['right_sha256']=rows[1]['sha256'];results['canonical_prefix'if normalized else'raw_prefix']=result
 require('.text'in results['raw_prefix']['executable_byte_differences'] and '.rodata'in results['raw_prefix']['allocated_section_differences'],'Fixture did not demonstrate path effect')
 require(results['canonical_prefix']['left_sha256']==results['canonical_prefix']['right_sha256'],'Normalized fixtures differ')
 return dict(results,abi='aarch64-linux-android24',same_source_sha256=hashlib.sha256(source.encode()).hexdigest(),fixture_only=True,fixture_count=4,apk_modified=False,historical_cause_proven=False,android_executed=False,limits='Synthetic sizeof(__FILE__) makes path changes observable. This causal example does not attribute every historical JNI difference to paths.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['ndk','work','output']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();r=experiment(a.ndk.resolve(),a.work.absolute());a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'normalized_equal':True,'fixture_count':4,'apk_modified':False}))
