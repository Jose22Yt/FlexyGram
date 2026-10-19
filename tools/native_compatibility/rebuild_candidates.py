"""Offline, isolated source rebuild experiment. Never edits wheels, APK or runtime locks.
Inputs must be the exact archives/FreeType commit in rebuild-sources.json.
All results remain candidates even when necessary static checks pass.
"""
from pathlib import Path
import argparse,hashlib,io,json,os,subprocess,tarfile,zipfile
from audit import elf
from acceptance import candidate_contract
from wheelhouse import verified

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify_archive(path,expected):
    if path.is_symlink() or not path.is_file() or digest(path)!=expected:
        raise ValueError('Source archive digest/type mismatch: '+path.name)

def patch_callback(source):
    old='xmlChar * name ATTRIBUTE_UNUSED)';new='const xmlChar * name ATTRIBUTE_UNUSED)'
    if source.count(old)!=1:raise ValueError('Reviewed callback patch no longer matches')
    return source.replace(old,new)

def environment(ndk,prefix):
    env=os.environ.copy()
    for key in ['CPATH','C_INCLUDE_PATH','CPLUS_INCLUDE_PATH','LIBRARY_PATH','LD_LIBRARY_PATH','BASH_ENV','CONFIG_SITE']:
        env.pop(key,None)
    tool=ndk/'toolchains/llvm/prebuilt/linux-x86_64/bin'
    env.update(CC=str(tool/'aarch64-linux-android24-clang'),AR=str(tool/'llvm-ar'),
               RANLIB=str(tool/'llvm-ranlib'),STRIP=str(tool/'llvm-strip'),
               CFLAGS='-O2 -fPIC',CPPFLAGS='-I'+str(prefix/'include'),
               LDFLAGS='-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384 -Wl,--undefined-version -L'+str(prefix/'lib'),
               PKG_CONFIG_LIBDIR=str(prefix/'lib/pkgconfig'),PKG_CONFIG_PATH=str(prefix/'lib/pkgconfig'),
               PATH=str(prefix/'bin')+':'+env['PATH'],SOURCE_DATE_EPOCH='1524096000')
    return env

def rebuild(sources,output,ndk,cmake,wheelhouse,manifest):
    for path in [sources,output,wheelhouse]:
        if path.is_symlink():raise ValueError('Symlink source/output/wheelhouse root is not allowed')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty candidate output directory')
    output.mkdir(parents=True,exist_ok=True)
    if '27.2.12479018' not in (ndk/'source.properties').read_text():raise ValueError('Exact reviewed NDK required')
    src=output/'sources';src.mkdir();prefix=output/'prefix';env=environment(ndk,prefix)
    for row in manifest['archives']:
        archive=sources/row['file'];verify_archive(archive,row['sha256'])
        with tarfile.open(archive) as tar:tar.extractall(src,filter='data')
    ft=sources/'freetype-git'
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ft,text=True).strip()
    if actual!=manifest['freetype_commit']:raise ValueError('FreeType source commit mismatch')
    # Export the immutable committed tree, excluding ignored/untracked files and .git hooks.
    data=subprocess.check_output(['git','archive','--format=tar',actual],cwd=ft)
    ftout=src/'freetype';ftout.mkdir()
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:tar.extractall(ftout,filter='data')
    commands=[]
    def run(args,cwd,log):
        commands.append({'args':args,'cwd':str(cwd.relative_to(output))})
        with log.open('a') as stream:subprocess.run(args,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
    packages=[('xz-5.2.4',['--disable-shared','--with-pic','--disable-xz','--disable-xzdec','--disable-lzmadec','--disable-lzmainfo','--disable-scripts','--disable-doc']),
              ('libxml2-2.9.8',['--without-python','--with-lzma']),
              ('libxslt-1.1.32',['--without-python','--without-crypto','--with-libxml-prefix='+str(prefix)])]
    for name,flags in packages:
        directory=src/name
        if name.startswith('libxslt'):
            f=directory/'libxslt/extensions.c';f.write_text(patch_callback(f.read_text()))
        log=output/(name+'.log')
        run(['./configure','--host=aarch64-linux-android','--prefix='+str(prefix),*flags],directory,log)
        run(['make','-j2'],directory,log);run(['make','install'],directory,log)
    ftbuild=output/'freetype-build'
    run([str(cmake),'-S',str(ftout),'-B',str(ftbuild),'-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),
         '-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-24','-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON',
         '-DBUILD_SHARED_LIBS=ON','-DFT_WITH_ZLIB=ON','-DCMAKE_DISABLE_FIND_PACKAGE_PNG=ON',
         '-DCMAKE_DISABLE_FIND_PACKAGE_BZip2=ON','-DCMAKE_DISABLE_FIND_PACKAGE_HarfBuzz=ON','-DCMAKE_BUILD_TYPE=Release',
         '-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384'],output,output/'freetype.log')
    run([str(cmake),'--build',str(ftbuild),'-j2'],output,output/'freetype.log')
    rows=[]
    for row in manifest['original_wheels']:
        archive=wheelhouse/row['filename']
        if not verified(archive,row):raise ValueError('Missing original wheel: '+row['filename'])
        with zipfile.ZipFile(archive) as z:
            for name in row['libraries']:
                original=elf(z.read('chaquopy/lib/'+name),name)
                after=elf((ftbuild/name if name=='libfreetype.so' else prefix/'lib'/name).read_bytes(),name)
                rows.append({'library':name,'contract':candidate_contract(original,after),
                             'candidate':{k:after[k] for k in ['sha256','soname','needed','load_4k','load_16k','android_note_api','relro']}})
    report={'libraries':rows,'commands':commands,'packaged':False,'active_lock_changed':False,
            'limits':'Independent source experiment, not a replacement. Optional feature/behavior parity and Android loader tests remain required.'}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['sources','output','ndk','cmake','wheelhouse']:p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args();m=json.loads(Path(__file__).with_name('rebuild-sources.json').read_text())
    report=rebuild(*(getattr(args,k).absolute() for k in ['sources','output','ndk','cmake','wheelhouse']),m)
    print(json.dumps({'built_candidates':len(report['libraries']),'packaged':False,'runtime_validated':False}))
