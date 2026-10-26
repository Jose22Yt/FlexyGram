#!/usr/bin/env python3
"""Deterministic inventory from pinned public Git objects. Never reads private build inputs."""
from functools import lru_cache
from pathlib import Path
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
BASE='8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881'
WORK1='ab7b16ff816e353d069c8bd064f5417d4dc22f92'
MAIN='db1bea24b7b705de33f8ff8c8e174011c153cac7'
BRAND=re.compile(r'exteraless|exteragram|nagram\s*x|nekogram',re.I)
KEYS={'AppName','AppNameBeta','NagramX','OpenExtera','CustomTitleHint'}
A='{http://schemas.android.com/apk/res/android}'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
@lru_cache(maxsize=512)
def blob(path,revision=BASE):return git('show',revision+':'+path)
def paths(revision=BASE):return git('ls-tree','-r','--name-only',revision).decode().splitlines()
def line(text,needle):
 pos=text.find(needle);return text.count('\n',0,max(0,pos))+1

def identity():
 candidates=git('grep','-i','-l','-I','-E','exteraless|exteraGram|Nagram ?X|Nekogram|name="AppName"|name="AppNameBeta"',BASE,'--','TMessagesProj/src').decode().splitlines()
 resources=[];literals=[]
 for qualified in sorted(candidates):
  path=qualified.split(':',1)[1];text=blob(path).decode('utf-8')
  if '/res/values' in path and path.endswith('.xml'):
   try:tree=ET.fromstring(text)
   except ET.ParseError:continue
   for child in tree:
    if child.tag!='string':continue
    key=child.get('name','');value=''.join(child.itertext())
    if key not in KEYS and not BRAND.search(value):continue
    kind='visible_client_brand' if key in KEYS else 'legal_credit_preserve' if re.search(r'credit|licen[cs]e|thanks|author|acknow|contributor',key,re.I) else 'review_visible_context'
    resources.append(dict(path=path,line=line(text,'name="'+key+'"'),key=key,value=value,classification=kind))
  elif path.endswith(('.java','.kt')):
   for n,source in enumerate(text.splitlines(),1):
    for match in re.finditer(r'"(?:[^"\\]|\\.)*"',source):
     value=match.group()[1:-1]
     if not BRAND.search(value):continue
     kind='upstream_url_review' if value.startswith(('https://','http://')) else 'internal_identifier_preserve' if re.fullmatch(r'[a-zA-Z0-9_.\-/]+',value) and ('.'in value or '_'in value or value.startswith('extera')) else 'visible_literal_review'
     literals.append(dict(path=path,line=n,value=value,classification=kind))
 references=[]
 raw=git('grep','-n','-I','-E',r'R.string.(AppName|NagramX|OpenExtera)|getAppName\(',BASE,'--','TMessagesProj/src/main/java','TMessagesProj/src/main/kotlin').decode()
 for entry in raw.splitlines():
  revision,path,n,source=entry.split(':',3);references.append(dict(path=path,line=int(n),expression=source.strip(),classification='call_site_resolve_resource_at_runtime'))
 manifest=ET.fromstring(blob('TMessagesProj/src/main/AndroidManifest.xml'))
 app=manifest.find('application')
 labels=[dict(component='application',label=app.get(A+'label'))]+[dict(component=x.get(A+'name'),label=x.get(A+'label'))for x in app if x.get(A+'label')]
 permissions=[dict(name=p.get(A+'name'),max_sdk=p.get(A+'maxSdkVersion'))for p in manifest.findall('uses-permission')]
 return dict(base=BASE,scope='All tracked src resource values and Java/Kotlin brand literals; declarations are findings, not proof of runtime visibility. Legal/internal rows are not automatic replacement targets.',resources=resources,literals=literals,brand_references=references,manifest_labels=labels,permissions=permissions,connected_alpha_overlay=blob('TMessagesProj/src/connectedAlpha/res/values/flexygram_identity.xml').decode(),counts=dict(resources=len(resources),literals=len(literals),permissions=len(permissions)))

def licenses():
 files=[]
 for path in paths():
  if not re.fullmatch(r'(LICENSE|NOTICE|COPYING)(\.[A-Za-z0-9.]+)?',Path(path).name,re.I):continue
  data=blob(path);text=data.decode('utf-8',errors='replace');family='UNRESOLVED'
  for needle,label in [('GNU GENERAL PUBLIC LICENSE','GPL (inspect version/exception)'),('GNU LESSER GENERAL PUBLIC LICENSE','LGPL (inspect version/exception)'),('Apache License','Apache (inspect notice)'),('MIT License','MIT (inspect notice)'),('Redistribution and use in source and binary forms','BSD-style (inspect exact clauses)')]:
   if needle.lower()in text.lower():family=label;break
  files.append(dict(path=path,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),family_hint=family,classification='heuristic_only_not_legal_clearance'))
 submodules=[]
 config=blob('.gitmodules').decode()
 for block in config.split('[submodule ')[1:]:
  m=re.search(r'path = (.+)\n\s*url = (.+)',block)
  if m:
   path,url=m.groups();entry=git('ls-tree',BASE,'--',path).decode().split();submodules.append(dict(path=path,url=url,commit=entry[2],license_status='requires_pinned_submodule_and_packaged_dependency_review'))
 return dict(base=BASE,root_license_unchanged_sha256=hashlib.sha256(blob('LICENSE')).hexdigest(),tracked_license_files=files,submodules=submodules,limits='License-file inventory is not an exhaustive packaged SBOM. Maven/AAR transitives, Python wheels, codecs, fonts, artwork and submodule notices need release-specific verification.')

def boundary():
 diff=git('diff','--name-only',BASE,WORK1).decode().splitlines()
 return dict(base=BASE,main=MAIN,work1_head=WORK1,work1_branch='integration/alpha1275-signature-performance-ui',work1_changed_files=diff,policy='No tracked application/build/distribution file is changed by this audit. Staged patches require review/rebase AFTER Alpha1275; not a merge authorization.',reserved=['header','composer','player','bubbles','launcher','manifest','navigation','auth','private delivery'])

def generate():return {'identity-inventory.json':identity(),'license-inventory.json':licenses(),'work1-boundary.json':boundary()}
if __name__=='__main__':
 out=ROOT/'docs/prebeta';out.mkdir(parents=True,exist_ok=True)
 for name,data in generate().items():(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'base':BASE,'resources':identity()['counts'],'license_files':len(licenses()['tracked_license_files']),'work1_changed_files':boundary()['work1_changed_files']}))
