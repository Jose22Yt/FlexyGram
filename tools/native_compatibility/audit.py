"""Read-only ELF/APK audit. Requires pyelftools, never loads a library.
PT_LOAD is checked separately from RELRO and zip packaging. Not an Android runtime test.
"""
from pathlib import Path
from io import BytesIO
import argparse,hashlib,json,struct,zipfile
from elftools.elf.elffile import ELFFile

def versions(e):
    needed={};defined={}
    section=e.get_section_by_name('.gnu.version_r')
    if section:
        for version,aux in section.iter_versions():
            for a in aux:needed[a['vna_other']&0x7fff]=(version.name,a.name)
    section=e.get_section_by_name('.gnu.version_d')
    if section:
        for version,aux in section.iter_versions():
            names=list(aux)
            if names:defined[version['vd_ndx']&0x7fff]=names[0].name
    return needed,defined

def elf(data,path):
    e=ELFFile(BytesIO(data));loads=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD']
    dynamic=e.get_section_by_name('.dynamic');needed=[];soname=None
    if dynamic:
        for tag in dynamic.iter_tags():
            if tag.entry.d_tag=='DT_NEEDED':needed.append(tag.needed)
            if tag.entry.d_tag=='DT_SONAME':soname=tag.soname
    need_versions,definitions=versions(e);vs=e.get_section_by_name('.gnu.version')
    undefined=[];exports=[];symbols=e.get_section_by_name('.dynsym')
    if symbols:
        for i,s in enumerate(symbols.iter_symbols()):
            if not s.name:continue
            vi=vs.get_symbol(i)['ndx'] if vs else None
            hidden=isinstance(vi,int) and bool(vi&0x8000);vi=(vi&0x7fff) if isinstance(vi,int) else vi
            if s['st_shndx']=='SHN_UNDEF':
                provider,version=need_versions.get(vi,(None,None))
                undefined.append({'name':s.name,'weak':s['st_info']['bind']=='STB_WEAK','provider':provider,'version':version})
            elif s['st_info']['bind'] in ['STB_GLOBAL','STB_WEAK'] and s['st_other']['visibility'] in ['STV_DEFAULT','STV_PROTECTED']:
                exports.append((s.name,definitions.get(vi)))
                if not hidden:exports.append((s.name,None))
    relro=[]
    for segment in e.iter_segments():
        if segment['p_type']=='PT_GNU_RELRO':
            start=segment['p_vaddr'];end=start+segment['p_memsz'];rounded=(end+16383)//16384*16384
            # Only allocated+writable content outside RELRO sharing its rounded last page is at risk.
            shared=[sec.name for sec in e.iter_sections() if (sec['sh_flags']&3)==3 and sec['sh_size'] and sec['sh_addr']<rounded and sec['sh_addr']+sec['sh_size']>end]
            relro.append({'start':start,'end':end,'end_aligned_16k':end%16384==0,'writable_sections_in_roundup':shared})
    android_note=None
    section=e.get_section_by_name('.note.android.ident')
    if section:
        for note in section.iter_notes():
            if note['n_name']=='Android' and isinstance(note['n_desc'],bytes) and len(note['n_desc'])>=4:
                android_note=struct.unpack(('<' if e.little_endian else '>')+'I',note['n_desc'][:4])[0]
    def aligned(page):
        return bool(loads) and all(s['p_align']>=page and not s['p_align']&(s['p_align']-1) and (s['p_vaddr']-s['p_offset'])%s['p_align']==0 and (s['p_vaddr']-s['p_offset'])%page==0 and s['p_filesz']<=s['p_memsz'] and s['p_offset']+s['p_filesz']<=len(data) for s in loads)
    return {'path':path,'sha256':hashlib.sha256(data).hexdigest(),'machine':e['e_machine'],'android_note_api':android_note,
            'soname':soname,'needed':needed,'load_segments':[{'offset':s['p_offset'],'vaddr':s['p_vaddr'],'filesz':s['p_filesz'],'memsz':s['p_memsz'],'align':s['p_align'],'flags':s['p_flags']} for s in loads],
            'load_4k':aligned(4096),'load_16k':aligned(16384),'relro':relro,'undefined':undefined,'exports':sorted(set(exports),key=lambda x:(x[0],x[1] or ''))}

def members(data,path,depth=0):
    if data.startswith(b'\x7fELF'):yield data,path
    elif data.startswith(b'PK'):
        if depth>=8:raise ValueError('Nested archive limit')
        with zipfile.ZipFile(BytesIO(data)) as z:
            if z.testzip() is not None:raise ValueError('ZIP CRC failed')
            if sum(x.file_size for x in z.infolist())>2**31:raise ValueError('Archive expansion limit')
            for name in z.namelist():
                if not name.endswith('/') and (name.endswith(('.so','.imy','.zip')) or name.startswith('lib/')):
                    yield from members(z.read(name),path+'!'+name,depth+1)

def providers(rows):
    result={}
    for r in rows:result.setdefault(r['soname'] or r['path'].rsplit('/',1)[-1],[]).append(r)
    return result

def check_symbols(rows,system):
    bundled=providers([r for r in rows if r['machine']=='EM_AARCH64']);all_providers={**system,**bundled}
    all_exports=set(x for r in rows if r['machine']=='EM_AARCH64' for x in map(tuple,r['exports']))
    for group in system.values():
        for r in group:all_exports.update(map(tuple,r['exports']))
    for r in rows:
        if r['machine']!='EM_AARCH64':
            r['api24_audit']='not_android_arm64';continue
        seen=set();closure={};todo=list(r['needed']);missing=[]
        while todo:
            name=todo.pop()
            if name in seen:continue
            seen.add(name)
            candidates=all_providers.get(name,[])
            if not candidates:missing.append(name)
            for provider in candidates:
                closure[provider['path']]=provider;todo.extend(provider['needed'])
        exports=set(map(tuple,r['exports']))
        for provider in closure.values():exports.update(map(tuple,provider['exports']))
        outside=[];unresolved=[];version_mismatch=[]
        for symbol in r['undefined']:
            if symbol['weak']:continue
            key=(symbol['name'],symbol['version'])
            if symbol['provider']:
                group=all_providers.get(symbol['provider'],[])
                if not any(key in map(tuple,p['exports']) for p in group):version_mismatch.append(symbol)
            if key not in exports:
                (outside if key in all_exports else unresolved).append(symbol)
        r['missing_needed_api24']=sorted(set(missing));r['strong_outside_needed_closure']=outside
        r['strong_unresolved_api24']=unresolved;r['version_provider_mismatches_api24']=version_mismatch
        r['weak_imports']=[s for s in r['undefined'] if s['weak']]
        r['api24_audit']='static_only'
    return rows

def audit(apk,ndk):
    data=apk.read_bytes();rows=[elf(b,p) for b,p in members(data,apk.name)]
    directory=ndk/'toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/aarch64-linux-android/24'
    if not directory.is_dir():raise ValueError('NDK API24 stubs not found')
    stubs=[elf(p.read_bytes(),p.name) for p in directory.glob('*.so') if p.read_bytes().startswith(b'\x7fELF')]
    check_symbols(rows,providers(stubs))
    for row in rows:row.pop('exports');row.pop('undefined')
    android=[r for r in rows if r['machine']=='EM_AARCH64']
    return {'apk_sha256':hashlib.sha256(data).hexdigest(),'libraries':rows,
            'summary':{'elf_total':len(rows),'android_arm64':len(android),'arm64_4k_pass':sum(r['load_4k'] for r in android),'arm64_16k_pass':sum(r['load_16k'] for r in android),
                       'other_machine':len(rows)-len(android),'missing_needed':sum(bool(r.get('missing_needed_api24')) for r in android),'strong_unresolved':sum(bool(r.get('strong_unresolved_api24')) for r in android),'version_mismatch':sum(bool(r.get('version_provider_mismatches_api24')) for r in android)},
            'limits':['Read-only ELF/version/provider audit, not a linker or Android execution.',
                      'Resolution outside DT_NEEDED closure is reported, never assumed safe; Chaquopy global Python symbols require runtime validation.',
                      'Weak symbols, dlopen/dlsym, namespaces, Java/JNI registration and execution paths require lab tests.',
                      'RELRO end misalignment alone is an advisory; writable overlap and PT_LOAD are reported separately.',
                      'AArch64 objects inside this Android APK are the target set; other-machine payloads remain visible, not silently dropped.']}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apk',type=Path,required=True);p.add_argument('--ndk',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.apk,a.ndk);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['summary']))
