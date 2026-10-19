"""Static APK verification. Does not execute Android code or certify runtime behavior."""
import sys,pathlib,hashlib,zipfile,io,struct,subprocess,json,tempfile,collections
apk=pathlib.Path(sys.argv[1]).resolve();out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
r={'apk_file':apk.name,'bytes':apk.stat().st_size,'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'archives':[],'native_files':[],'zip_native_entries':[],'python_distributions':[],'pyc_magic_counts':{},'short_pyc_headers':[],'limits':['Static analysis only; no Android execution.','DT_NEEDED names do not prove symbol/version compatibility or dynamically loaded library closure.','RELRO writable-tail overlaps are structural risk indicators, not observed crashes.']}
logs=(out/'readelf-all.txt').open('w');tmp=tempfile.TemporaryDirectory();counter=0
def walk(data,label,depth=0):
 global counter
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  bad=z.testzip();r['archives'].append({'path':label,'entries':len(z.infolist()),'crc_error':bad})
  for i in z.infolist():
   if i.is_dir():continue
   b=z.read(i);p=label+'!'+i.filename
   if i.filename.endswith('.dist-info/METADATA'):
    import email.parser
    meta=email.parser.BytesParser().parsebytes(b,headersonly=True)
    r['python_distributions'].append({'name':meta.get('Name'),'version':meta.get('Version'),'path':p})
   if i.filename.endswith('.pyc'):
    magic=b[:4].hex();r['pyc_magic_counts'][magic]=r['pyc_magic_counts'].get(magic,0)+1
    if len(b)<16:r['short_pyc_headers'].append(p)
   if depth==0 and i.filename.startswith('lib/') and i.filename.endswith('.so'):
    h=data[i.header_offset:i.header_offset+30];v=struct.unpack('<IHHHHHIIIHH',h);offset=i.header_offset+30+v[-2]+v[-1]
    r['zip_native_entries'].append({'path':i.filename,'compression':i.compress_type,'data_offset':offset,'remainder_16k':offset%16384,'requires_direct_mmap_alignment':i.compress_type==0})
   if i.filename.endswith(('.imy','.zip')) and depth<3 and zipfile.is_zipfile(io.BytesIO(b)):walk(b,p,depth+1)
   if not b.startswith(b'\x7fELF'):continue
   counter+=1;f=pathlib.Path(tmp.name)/str(counter);f.write_bytes(b)
   result=subprocess.run(['readelf','-W','-h','-l','-d','-S',str(f)],text=True,capture_output=True);logs.write(p+'\n'+result.stdout+result.stderr+'\n')
   row={'path':p,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'readelf_exit':result.returncode}
   if b[4]!=2 or b[5]!=1:row['unsupported_elf_parser']=True;r['native_files'].append(row);continue
   e=struct.unpack_from('<16sHHIQQQIHHHHHH',b);row['section_headers_available']=bool(e[6] and e[12]);row.update({'elf_class':64,'machine':e[2]});ph=[]
   for n in range(e[10]):
    t,flags,offset,vaddr,paddr,filesz,memsz,align=struct.unpack_from('<IIQQQQQQ',b,e[5]+n*e[9]);ph.append({'type':t,'flags':flags,'offset':offset,'vaddr':vaddr,'filesz':filesz,'memsz':memsz,'align':align})
   loads=[x for x in ph if x['type']==1];row['pt_load']=loads
   row['load_alignment_4k']=all(x['align']>=4096 and (x['vaddr']-x['offset'])%4096==0 for x in loads)
   row['load_sizes_valid']=all(x['filesz']<=x['memsz'] and x['offset']+x['filesz']<=len(b) for x in loads)
   shstr=struct.unpack_from('<IIQQQQIIQQ',b,e[6]+e[13]*e[11]);names=b[shstr[4]:shstr[4]+shstr[5]]
   row['load_alignment_16k']=all(x['align']>=16384 and (x['vaddr']-x['offset'])%16384==0 for x in loads)
   row['gnu_relro']=[]
   for seg in ph:
    if seg['type']!=0x6474e552:continue
    start=seg['vaddr'];end=start+seg['memsz'];lo=start//16384*16384;hi=(end+16383)//16384*16384
    # File-backed SHF_ALLOC|SHF_WRITE sections outside exact RELRO but in protected pages.
    overlap=[]
    for n in range(e[12]):
     sh=struct.unpack_from('<IIQQQQIIQQ',b,e[6]+n*e[11]);flags,addr,size=sh[2],sh[3],sh[5]
     if flags&3!=3 or not size:continue
     a=max(addr,lo);c=min(addr+size,hi)
     if a<c and (a<start or c>end):overlap.append({'section_index':n,'section_name':names[sh[0]:].split(b'\0')[0].decode('utf-8','replace'),'type':sh[1],'vaddr':addr,'size':size,'intersection':[a,c]})
    row['gnu_relro'].append({'vaddr':start,'memsz':seg['memsz'],'end_mod_16k':end%16384,'page_protected_range':[lo,hi],'writable_sections_outside_relro_in_same_pages':overlap,'nonpadding_writable_overlap':any(x['section_name'] not in ['.relro_padding'] for x in overlap)})
   import re
   row['needed']=re.findall(r'\(NEEDED\).*?\[(.*?)\]',result.stdout);soname=re.findall(r'\(SONAME\).*?\[(.*?)\]',result.stdout);row['soname']=soname[0] if soname else None
   r['native_files'].append(row)
walk(apk.read_bytes(),apk.name);logs.close()
arm=[x for x in r['native_files'] if x.get('machine')==183];installed=[x for x in arm if '!lib/' in x['path']]
provided={x['path'].split('!')[-1].split('/')[-1] for x in arm}|{x['soname'] for x in arm if x.get('soname')}
system={'libc.so','libdl.so','libm.so','liblog.so','libandroid.so','libz.so','libjnigraphics.so','libOpenSLES.so','libEGL.so','libGLESv2.so','libGLESv3.so','libmediandk.so','libvulkan.so','libaaudio.so','libnativewindow.so','libstdc++.so'}
for x in arm:x['needed_not_found_in_apk_or_common_android_system_allowlist']=[n for n in x['needed'] if n not in provided|system]
r['summary']={'elf_total':len(r['native_files']),'arm64_total':len(arm),'installed_arm64':len(installed),'apk_abis':sorted({x['path'].split('/')[1] for x in r['zip_native_entries']}),'arm64_load_alignment_failures':[x['path'] for x in arm if not x['load_alignment_16k']],'non_arm64_elf':[x['path'] for x in r['native_files'] if x.get('machine')!=183],'relro_end_unaligned_count':sum(any(s['end_mod_16k'] for s in x['gnu_relro']) for x in arm),'relro_writable_overlap_count':sum(any(s['nonpadding_writable_overlap'] for s in x['gnu_relro']) for x in arm),'unresolved_needed':[{'path':x['path'],'names':x['needed_not_found_in_apk_or_common_android_system_allowlist']} for x in arm if x['needed_not_found_in_apk_or_common_android_system_allowlist']]}
(out/'apk-audit.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:r[k] for k in ['apk_file','bytes','sha256','summary']},indent=2))
