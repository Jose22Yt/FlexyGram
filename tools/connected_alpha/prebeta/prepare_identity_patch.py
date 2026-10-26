#!/usr/bin/env python3
"""Prepare reviewed visible-brand substitutions without changing application files."""
import difflib,re,subprocess
from pathlib import Path
from scan import BASE,ROOT,blob,paths

def prepare():
 changes={}
 for path in paths():
  if not re.match(r'TMessagesProj/src/main/res/values[^/]*/.*\.xml$',path):continue
  before=blob(path).decode()
  if not re.search(r'<string name="(?:AppName|AppNameBeta|NagramX|OpenExtera|CustomTitleHint)"',before):continue
  after=before
  for key,value in [('AppName','FlexyGram'),('AppNameBeta','FlexyGram Beta'),('NagramX','FlexyGram'),('OpenExtera','FlexyGram')]:
   after=re.sub(r'(<string name="'+key+r'"[^>]*>).*?(</string>)',lambda m:m[1]+value+m[2],after,flags=re.S)
  if '/values/'in path:after=re.sub(r'(<string name="CustomTitleHint"[^>]*>).*?(</string>)',r'\g<1>Leave blank to use FlexyGram\2',after,flags=re.S)
  if before!=after:changes[path]=(before,after)
 for language,hint in [('values','Leave blank to use FlexyGram'),('values-es','Deja el campo vacío para usar FlexyGram'),('values-ru','Оставьте пустым, чтобы использовать FlexyGram')]:
  path=f'TMessagesProj/src/connectedAlpha/res/{language}/flexygram_identity.xml'
  before=blob(path).decode() if path in paths() else ''
  after='<?xml version="1.0" encoding="utf-8"?>\n<!-- Visible labels only. Preserve all existing resource keys and component identities. -->\n<resources>\n'
  for key,value in [('AppName','FlexyGram Alpha'),('AppNameBeta','FlexyGram Alpha'),('NagramX','FlexyGram Alpha'),('OpenExtera','FlexyGram'),('CustomTitleHint',hint)]:
   after+='    <string name="'+key+'">'+value+'</string>\n'
  after+='</resources>\n';changes[path]=(before,after)
 path='TMessagesProj/src/main/java/org/telegram/messenger/LocaleController.java';before=blob(path).decode();after=before.replace('return "exteraless";','return "FlexyGram";');assert after!=before;changes[path]=(before,after)
 patch=[]
 for path,(before,after)in sorted(changes.items()):
  patch.append('diff --git a/'+path+' b/'+path+'\n')
  if not before:patch.append('new file mode 100644\n')
  patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+path if before else '/dev/null',tofile='b/'+path))
 return ''.join(patch),changes
if __name__=='__main__':
 patch,changes=prepare();out=ROOT/'tools/connected_alpha/prebeta/android-identity.patch';out.write_text(patch);print('Staged only:',len(changes),'files; application worktree unchanged')
