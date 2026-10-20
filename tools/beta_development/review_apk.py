"""Static review of the NEW offline beta APK. No signing, Android loading or installation.

Reuses existing ELF and retired-key scanners; never changes Diagnostic pins/contracts.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools/native_compatibility'),str(ROOT/'tests/translation_safety')]
from audit import audit
from acceptance import artifact_acceptance
from artifact_gate import scan

PACKAGE='io.github.jose22yt.flexygram.beta.development'
ENTRY='org.telegram.ui.beta.BetaPreviewActivity'
LAUNCHER='org.telegram.messenger.ExteralessIcon'
A='{http://schemas.android.com/apk/res/android}'


def require(value,message):
    if not value:raise ValueError(message)


def command(args):
    return subprocess.run(list(map(str,args)),check=True,capture_output=True,text=True).stdout


def binary_manifest(apk,aapt2):
    text=command([aapt2,'dump','xmltree',apk,'--file','AndroidManifest.xml'])
    stack=[];root=None
    for line in text.splitlines():
        match=re.match(r'(\s*)E: ([\w-]+)',line)
        if match:
            indent=len(match[1]);node=ET.Element(match[2])
            while stack and stack[-1][0]>=indent:stack.pop()
            if stack:stack[-1][1].append(node)
            else:root=node
            stack.append((indent,node));continue
        match=re.match(r'\s*A: ([^=( ]+)(?:\([^)]*\))?=(.*)',line)
        if match and stack:
            name,value=match.groups()
            if value.startswith('"'):value=value.split('"')[1]
            elif '(type 0x12)'in value:value='true'if value.endswith('0xffffffff')else'false'
            if name.endswith(':protectionLevel'):
                try:
                    if int(value.split(')')[-1],0)==2:value='signature'
                except ValueError:pass
            if name.startswith('android:'):name=A+name[8:]
            elif name.startswith('http://schemas.android.com/apk/res/android:'):name=A+name.rsplit(':',1)[1]
            stack[-1][1].set(name,value)
    require(root is not None and root.get('package')==PACKAGE,'Wrong beta APK package')
    sdk=root.findall('uses-sdk')
    require(len(sdk)==1 and int(sdk[0].get(A+'minSdkVersion','-1'),0)==24 and
            int(sdk[0].get(A+'targetSdkVersion','-1'),0)==36,'Unexpected binary SDK contract')
    permissions=[n.get(A+'name')for n in root.findall('uses-permission')]
    require(set(permissions)=={'android.permission.ACCESS_NETWORK_STATE',PACKAGE+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'},'Unexpected beta permission')
    custom=root.findall('permission')
    require(len(custom)==1 and custom[0].get(A+'name')==PACKAGE+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'and custom[0].get(A+'protectionLevel')=='signature','Invalid receiver signature permission')
    require(not root.findall('uses-permission-sdk-23'),'Unexpected SDK-specific permission')
    app=root.find('application');require(app is not None,'Application missing')
    require(app.get(A+'name')=='org.telegram.messenger.ApplicationLoader','Wrong beta application initializer')
    require(app.get(A+'debuggable')=='true','Development APK must be Debug')
    require(app.get(A+'allowBackup')=='false'and not app.get(A+'backupAgent'),'Backup/session restoration enabled')
    require(app.get(A+'usesCleartextTraffic')=='false','Cleartext capability unexpectedly enabled')
    rows=[]
    for node in app:
        if node.tag not in ('activity','activity-alias','provider','service','receiver'):continue
        enabled=node.get(A+'enabled','true')!='false'
        exported=node.get(A+'exported')
        exported=(node.tag!='provider'and bool(node.findall('intent-filter')))if exported is None else exported=='true'
        name=node.get(A+'name');authority=node.get(A+'authorities')
        if authority:require(all(x.startswith(PACKAGE+'.')for x in authority.split(';')),'Foreign authority')
        if node.tag in ('service','receiver','provider'):
            if name=='ru.noties.jlatexmath.JLatexMathInitProvider':require(enabled and not exported,'Rendering provider exposure')
            else:require(not enabled and not exported,'Unexpected active external component')
        if node.tag=='activity':require(not exported,'Directly exported activity')
        rows.append(dict(type=node.tag,name=name,enabled=enabled,exported=exported,authority=authority))
    public=[x for x in rows if x['enabled']and x['exported']]
    require(len(public)==1 and public[0]['name']==LAUNCHER,'Unexpected exported entry point')
    alias=next(n for n in app.findall('activity-alias')if n.get(A+'name')==LAUNCHER)
    require(alias.get(A+'targetActivity')==ENTRY,'Wrong beta launcher target')
    filters=alias.findall('intent-filter')
    require(len(filters)==1 and {n.get(A+'name')for n in filters[0].findall('action')}=={'android.intent.action.MAIN'} and
            'android.intent.category.LAUNCHER' in {n.get(A+'name')for n in filters[0].findall('category')} and
            {n.get(A+'name')for n in filters[0].findall('category')} <= {'android.intent.category.LAUNCHER','android.intent.category.MULTIWINDOW_LAUNCHER'} and
            not filters[0].findall('data'),'Unexpected launcher intent')
    target=next(n for n in app.findall('activity')if n.get(A+'name')==ENTRY)
    require(target.get(A+'enabled','true')=='true','Beta target disabled')
    return dict(package=PACKAGE,permissions=permissions,components=rows,enabled_exported=public)


def review(args):
    raw=args.apk.read_bytes();scope=hashlib.sha256((ROOT/'gradle/beta-development.json').read_bytes()).hexdigest()+':betaDevelopment'
    badging=command([args.build_tools/'aapt2','dump','badging',args.apk])
    require(re.search(r"(?m)^(?:minSdkVersion|sdkVersion):'24'$",badging)and "targetSdkVersion:'36'"in badging,'Unexpected Android SDK contract')
    constants=command([args.javap,'-constants','-p','-classpath',args.classes,'org.telegram.messenger.BuildConfig'])
    require('APPLICATION_ID = "'+PACKAGE+'";'in constants and 'APP_ID = 0;'in constants and 'APP_HASH = "";'in constants,'Compiled beta identity/API configuration mismatch')
    require('ISOLATED_DIAGNOSTIC = true;'in constants and 'FLEXYGRAM_POLICY_SCOPE = "'+scope+'";'in constants,'Compiled isolation/scope mismatch')
    for name in ('AUTHENTICATION','TELEGRAMTRANSPORT','PUSH','TRANSLATION','PLUGINS','SESSIONRESTORE'):
        require('FLEXYGRAM_CAP_'+name+' = false;'in constants,'Compiled external capability enabled')
    for name in ('FLEXYGRAM_FCM_ENABLED','FLEXYGRAM_UNIFIED_PUSH_ENABLED'):
        require(name+' = false;'in constants,'Compiled push capability enabled')
    for name in ('FLEXYGRAM_FCM_API_KEY','FLEXYGRAM_FCM_PROJECT_ID','FLEXYGRAM_FCM_APP_ID','FLEXYGRAM_FCM_SENDER_ID','FLEXYGRAM_UNIFIED_GATEWAY','FLEXYGRAM_UNIFIED_DISTRIBUTOR'):
        require(name+' = "";'in constants,'Compiled service configuration not empty')
    with zipfile.ZipFile(args.apk)as z:
        require(z.testzip()is None and len(z.namelist())==len(set(z.namelist())),'Invalid APK ZIP')
        require(not any(re.match(r'META-INF/[^/]+\.(RSA|DSA|EC|SF)$',n,re.I)for n in z.namelist()),'Unexpected JAR signing material')
        require(all(n.startswith('lib/arm64-v8a/')for n in z.namelist()if n.startswith('lib/')and n.endswith('.so')),'Wrong installable native ABI')
        jni=z.read('lib/arm64-v8a/libtmessages.49.so')
        needle=('FLEXYGRAM_POLICY:'+scope+':auth=0:transport=0:push=0:translation=0:plugins=0:restore=0').encode()
        require(needle in jni,'Missing compiled beta native policy')
        dex=b''.join(z.read(n)for n in z.namelist()if re.fullmatch(r'classes(?:\d+)?\.dex',n))
        require(b'Lorg/telegram/ui/beta/BetaPreviewActivity;'in dex and b'Lorg/telegram/ui/beta/LatestNavigation;'in dex,'Missing compiled beta entry/navigation')
    require(b'APK Sig Block 42'not in raw,'Unexpected APK signing block')
    signature=subprocess.run([str(args.build_tools/'apksigner'),'verify','--verbose','--print-certs',str(args.apk)],capture_output=True,text=True)
    require(signature.returncode!=0 and 'certificate SHA-256 digest:'not in signature.stdout,'APK unexpectedly signed')
    command([args.build_tools/'zipalign','-c','-P','16','-v','4',args.apk])
    manifest=binary_manifest(args.apk,args.build_tools/'aapt2')
    elf=audit(args.apk,args.ndk);acceptance=artifact_acceptance(elf)
    require(not acceptance['blockers'],'Native static blockers remain')
    wanted=json.loads((ROOT/'docs/security-p04c/evidence-unsigned-rebuild-20261020/unsigned-apk-receipt.json').read_text())['packaged_rebuilt_elf']
    for name,digest in wanted.items():
        matches=[x for x in elf['libraries']if x['path'].endswith('/'+name)]
        require(len(matches)==1 and matches[0]['sha256']==digest,'Rebuilt wheel ELF mismatch: '+name)
    findings=scan(raw,json.loads((ROOT/'tests/translation_safety/retired_fingerprints.json').read_text()),require_apk=True)
    require(findings['passed'],'Retired key/dependency finding; inspect counts without exposing values')
    return dict(status='BETA_UNSIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID',apk_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),
                manifest=manifest,native_summary=elf['summary'],native_acceptance=acceptance,
                jni_sha256=hashlib.sha256(jni).hexdigest(),native_policy_scope=scope,rebuilt_elf_exact=True,
                compiled_buildconfig_closed=True,min_sdk=24,target_sdk=36,
                retired_scan=findings,signature='absent',zipalign_16k=True,android_executed=False,distribution_allowed=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('apk','build-tools','ndk','classes','javap','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();result=review(args);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ('status','apk_sha256','bytes','native_summary','signature')}))
