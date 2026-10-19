from pathlib import Path
import os,subprocess,tarfile,io,json
from rebuild_candidates import verify_archive
import argparse
p=argparse.ArgumentParser(description='Host-only source libraries for local functional fixtures; never Android certification.')
p.add_argument('--workspace',type=Path,required=True)
a=p.parse_args();r=a.workspace.resolve();out=r/'host-compat'
if out.exists() and any(out.iterdir()):raise ValueError('Use an empty host fixture output directory')
manifest=json.loads(Path(__file__).with_name('rebuild-sources.json').read_text())
for row in manifest['archives']:verify_archive(r/'rebuild-sources'/row['file'],row['sha256'])
src=out/'sources';src.mkdir(parents=True,exist_ok=True);prefix=out/'prefix';env=os.environ.copy();env.update(CFLAGS='-O2 -fPIC',LDFLAGS='-L'+str(prefix/'lib'),CPPFLAGS='-I'+str(prefix/'include'),LD_LIBRARY_PATH=str(prefix/'lib'),PKG_CONFIG_LIBDIR=str(prefix/'lib/pkgconfig'),PATH=str(prefix/'bin')+':'+env['PATH'])
for f in ['xz-5.2.4-complete.tar.xz','libxml2-2.9.8.tar.xz','libxslt-1.1.32.tar.xz']:
 with tarfile.open(r/'rebuild-sources'/f) as t:t.extractall(src,filter='data')
log=open(out/'build.log','w')
for n,flags in [('xz-5.2.4',['--disable-shared','--with-pic','--disable-xz','--disable-xzdec','--disable-lzmadec','--disable-lzmainfo','--disable-scripts','--disable-doc']),('libxml2-2.9.8',['--without-python','--with-lzma']),('libxslt-1.1.32',['--without-python','--without-crypto','--with-libxml-prefix='+str(prefix)])]:
 p=src/n
 for args in [['./configure','--prefix='+str(prefix),*flags],['make','-j2'],['make','install']]:subprocess.run(args,cwd=p,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
ft=src/'freetype';ft.mkdir();data=subprocess.check_output(['git','archive','86bc8a95056c97a810986434a3f268cbe67f2902'],cwd=r/'rebuild-sources/freetype-git')
with tarfile.open(fileobj=io.BytesIO(data)) as t:t.extractall(ft,filter='data')
cmake=r/'android-tools/sdk/cmake/3.31.6/bin/cmake'
for args in [[str(cmake),'-S',str(ft),'-B',str(out/'ft'),'-DBUILD_SHARED_LIBS=ON','-DCMAKE_DISABLE_FIND_PACKAGE_PNG=ON','-DCMAKE_DISABLE_FIND_PACKAGE_BZip2=ON','-DCMAKE_DISABLE_FIND_PACKAGE_HarfBuzz=ON','-DFT_WITH_ZLIB=ON','-DCMAKE_BUILD_TYPE=Release'],[str(cmake),'--build',str(out/'ft'),'-j2']]:subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
print('Host source libraries built (not Android).')
