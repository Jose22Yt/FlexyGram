"""Explicit unsigned startup diagnostic identity. Never accepts a realAlpha/Diagnostic/Beta APK."""
import argparse,hashlib,json,re,subprocess,zipfile
from pathlib import Path
import review_apk as base
PACKAGE='io.github.jose22yt.flexygram.realalpha.startupdiagnostic'
APP='org.telegram.ui.realalpha.diagnostics.StartupDiagnosticApplication'
REPORT='org.telegram.ui.realalpha.diagnostics.StartupReportActivity'
PROBE='org.telegram.ui.realalpha.RealAlphaActivity'
A=base.A

def check(value,message):
 if not value:raise ValueError(message)

def validate(root):
 check(root.get('package')==PACKAGE,'Wrong startup diagnostic identity')
 sdk=root.find('uses-sdk');check(int(sdk.get(A+'minSdkVersion'),0)==24 and int(sdk.get(A+'targetSdkVersion'),0)==36,'Wrong SDK contract')
 permissions=[n.get(A+'name') for n in root.findall('uses-permission')]
 check(len(permissions)==2 and set(permissions)=={'android.permission.ACCESS_NETWORK_STATE',PACKAGE+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'},'Unexpected permission')
 check(not root.findall('uses-permission-sdk-23'),'Unexpected permission form')
 custom=root.findall('permission')
 check(len(custom)==1 and custom[0].get(A+'name')==PACKAGE+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION' and custom[0].get(A+'protectionLevel')=='signature','Unexpected custom permission')
 app=root.find('application');check(app.get(A+'name')==APP,'Wrong diagnostic application')
 check(app.get(A+'debuggable')=='true','Diagnostic must remain debuggable')
 for name in ('allowBackup','restoreAnyVersion','fullBackupContent','usesCleartextTraffic'):
  check(app.get(A+name)=='false','Open backup/cleartext capability')
 check(not app.get(A+'backupAgent'),'Unexpected backup agent')
 check(not any(app.findall(n) for n in ('service','receiver','activity-alias')),'Unexpected external component')
 activities=app.findall('activity');check(len(activities)==2,'Wrong activity count')
 byname={n.get(A+'name'):n for n in activities};check(set(byname)=={REPORT,PROBE},'Wrong startup components')
 report=byname[REPORT];probe=byname[PROBE]
 check(report.get(A+'exported')=='true' and not report.get(A+'process'),'Reporter not isolated from probe')
 check(probe.get(A+'exported')=='false' and probe.get(A+'process')==':startup_probe','Probe exposure/process mismatch')
 check(not probe.findall('intent-filter'),'Probe cannot be a launcher or deep link')
 filters=report.findall('intent-filter');check(len(filters)==1,'Wrong report filters')
 check([n.get(A+'name') for n in filters[0].findall('action')]==['android.intent.action.MAIN'],'Wrong report action')
 check([n.get(A+'name') for n in filters[0].findall('category')]==['android.intent.category.LAUNCHER'],'Wrong report category')
 check(not filters[0].findall('data'),'Unexpected link data')
 providers=app.findall('provider');check(len(providers)==1,'Unexpected provider')
 provider=providers[0];check(provider.get(A+'name')=='ru.noties.jlatexmath.JLatexMathInitProvider' and provider.get(A+'exported')=='false' and provider.get(A+'process')==':startup_probe' and provider.get(A+'authorities')==PACKAGE+'.jlatexmathinitprovider','Provider process/identity mismatch')
 metadata={n.get(A+'name'):n.get(A+'value') for n in app.findall('meta-data')}
 check(metadata.get('firebase_messaging_auto_init_enabled')=='false' and metadata.get('firebase_analytics_collection_deactivated')=='true' and metadata.get('firebase_crashlytics_collection_enabled')=='false','Remote service metadata mismatch')
 return {'package':PACKAGE,'launcher':REPORT,'probe':PROBE,'application':APP,'probe_process':':startup_probe','permissions':permissions,'no_internet':True,'restore_disabled':True}

def binary_root(apk,aapt):
 # Reuse only the binary XML parser. Its validator is deliberately NOT patched or relaxed.
 text=base.command([aapt,'dump','xmltree',apk,'--file','AndroidManifest.xml'])
 stack=[];root=None
 for line in text.splitlines():
  m=re.match(r'(\s*)E: ([\w-]+)',line)
  if m:
   indent=len(m[1]);node=base.ET.Element(m[2])
   while stack and stack[-1][0]>=indent:stack.pop()
   if stack:stack[-1][1].append(node)
   else:root=node
   stack.append((indent,node));continue
  m=re.match(r'\s*A: ([^=( ]+)(?:\([^)]*\))?=(.*)',line)
  if m and stack:
   name,value=m.groups()
   if value.startswith('"'):value=value.split('"')[1]
   elif '(type 0x12)' in value:value='true' if value.endswith('0xffffffff') else 'false'
   if name.endswith(':protectionLevel'):
    try:
     if int(value.split(')')[-1],0)==2:value='signature'
    except ValueError:pass
   if name.startswith('android:'):name=A+name[8:]
   elif name.startswith('http://schemas.android.com/apk/res/android:'):name=A+name.rsplit(':',1)[1]
   stack[-1][1].set(name,value)
 return root

def review(args):
 raw=args.apk.read_bytes();manifest=validate(binary_root(args.apk,args.build_tools/'aapt2'))
 check(manifest==validate(base.ET.parse(args.merged_manifest).getroot()),'Actual merged/binary manifest mismatch')
 constants=base.command([args.javap,'-constants','-p','-classpath',args.classes,'org.telegram.messenger.BuildConfig'])
 for line in ['APPLICATION_ID = "'+PACKAGE+'";','BUILD_TYPE = "startupDiagnostic";','FLEXYGRAM_VARIANT = "realAlpha";','ISOLATED_DIAGNOSTIC = true;','APP_ID = 0;','APP_HASH = "";','DEBUG_TOOLS = false;']:
  check(line in constants,'Wrong compiled startup profile')
 for cap in ('AUTHENTICATION','TELEGRAMTRANSPORT','PUSH','TRANSLATION','PLUGINS','SESSIONRESTORE'):
  check('FLEXYGRAM_CAP_'+cap+' = false;' in constants,'External capability enabled')
 with zipfile.ZipFile(args.apk) as z:
  check(z.testzip()is None and len(z.namelist())==len(set(z.namelist())),'Invalid ZIP')
  check(not any(re.match(r'META-INF/[^/]+\.(RSA|DSA|EC|SF)$',n,re.I) for n in z.namelist()),'Unexpected JAR signature')
  dex=b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes(?:\d+)?\.dex',n))
  for desc in [REPORT,APP,'org.telegram.messenger.StartupTrace','org.telegram.messenger.StartupFailureSanitizer']:
   check(('L'+desc.replace('.','/')+';').encode()in dex,'Missing diagnostic DEX class')
  check('resources.arsc' in z.namelist() and any(n.startswith('res/') for n in z.namelist()),'Missing resources')
  check(any(n.startswith('assets/chaquopy/') for n in z.namelist()),'Missing Chaquopy')
  jni=z.read('lib/arm64-v8a/libtmessages.49.so')
  scope=hashlib.sha256((base.ROOT/'gradle/real-alpha.json').read_bytes()).hexdigest()+':realAlpha'
  check(('FLEXYGRAM_POLICY:'+scope+':auth=0:transport=0:push=0:translation=0:plugins=0:restore=0').encode()in jni,'Native policy is not closed')
  check(all(n.startswith('lib/arm64-v8a/') for n in z.namelist() if n.startswith('lib/')and n.endswith('.so')),'Wrong installable ABI')
 check(b'APK Sig Block 42'not in raw,'Unexpected APK signature')
 sig=subprocess.run([str(args.build_tools/'apksigner'),'verify','--print-certs',str(args.apk)],capture_output=True,text=True)
 check(sig.returncode!=0 and 'certificate SHA-256 digest:'not in sig.stdout,'Unexpected signed diagnostic')
 base.command([args.build_tools/'zipalign','-c','-P','16','-v','4',args.apk])
 base.verify_dex_linkage(args.apk,args.build_tools/'dexdump')
 for cls in ('org.telegram.messenger.ApplicationLoader','org.telegram.messenger.NativeLoader','org.telegram.ui.LaunchActivity','org.telegram.ui.DialogsActivity','org.telegram.ui.realalpha.RealAlphaBootstrap'):
  compiled=base.command([args.javap,'-c','-p','-classpath',args.classes,cls])
  check('org/telegram/messenger/StartupTrace.'in compiled,'Generated startup overlay missing from compile')
 elf=base.audit(args.apk,args.ndk);base.check_native_inventory(elf);accept=base.artifact_acceptance(elf)
 check(not accept['blockers'],'Native blockers')
 wanted=json.loads((base.ROOT/'docs/security-p04c/evidence-unsigned-rebuild-20261020/unsigned-apk-receipt.json').read_text())['packaged_rebuilt_elf']
 for name,sha in wanted.items():
  rows=[x for x in elf['libraries'] if x['path'].endswith('/'+name)]
  check(len(rows)==1 and rows[0]['sha256']==sha,'Rebuilt ELF mismatch')
 findings=base.scan(raw,json.loads((base.ROOT/'tests/translation_safety/retired_fingerprints.json').read_text()),require_apk=True)
 check(findings['passed'],'Configuration/retired-key scanner failed')
 return {'status':'STARTUP_DIAGNOSTIC_UNSIGNED_ONLY_PENDING_ANDROID','apk_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'manifest':manifest,'native_summary':elf['summary'],'native_acceptance':accept,'signature':'absent','zipalign_4k_16k':True,'native_ui_dex_linkage':True,'generated_hooks_compiled':True,'retired_scan':findings,'android_executed':False,'root_cause_confirmed':False,'distribution_allowed':False}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('apk','build-tools','ndk','classes','javap','merged-manifest','output'):p.add_argument('--'+name,type=Path,required=True)
 args=p.parse_args();result=review(args);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
