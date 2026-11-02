#!/usr/bin/env python3
"""Full, authorized local Connected Alpha build; never uploads APK bytes to a public service."""
import argparse,hashlib,json,os,re,shutil,stat,subprocess,sys
from pathlib import Path
from ci_inputs import stage,fingerprint
ROOT=Path(__file__).resolve().parents[2]
CERT='c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c'
APP='io.github.jose22yt.flexygram.alpha'
def load_private_inputs(path):
 path=Path(path).resolve(strict=True)
 if path.is_relative_to(ROOT) or stat.S_IMODE(path.stat().st_mode)&0o077:
  raise ValueError('Build inputs must be outside the checkout and readable only by their owner')
 data=json.loads(path.read_text())
 if fingerprint(data.get('ALPHA_CERTIFICATE_SHA256',''))!=CERT:raise ValueError('Independent authorized certificate differs')
 return {k:str(v)for k,v in data.items()}
def redact(text,values):
 for value in sorted(set(values),key=len,reverse=True):
  if value:text=text.replace(value,'[REDACTED]')
 return text

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',required=True,type=Path);p.add_argument('--sdk-root',required=True,type=Path);p.add_argument('--jdk-root',required=True,type=Path);p.add_argument('--python',required=True,type=Path);p.add_argument('--wheelhouse',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
 args=p.parse_args();os.umask(0o077);secret=load_private_inputs(args.inputs);out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 sdk=args.sdk_root.resolve();jdk=args.jdk_root.resolve();py=args.python.resolve();wheel=args.wheelhouse.resolve()
 if not (wheel/'provenance.json').is_file():raise ValueError('Verified reconstructed wheelhouse is required')
 status=subprocess.check_output(['git','submodule','status','--recursive'],cwd=ROOT,text=True)
 if any(line.startswith(('+','-','U'))for line in status.splitlines()):raise ValueError('Native submodule does not match its pinned commit')
 if subprocess.check_output(['git','diff','HEAD','--','TMessagesProj/jni'],cwd=ROOT):raise ValueError('Native source worktree is modified')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 env=os.environ.copy();env.update(secret);env.update(JAVA_HOME=str(jdk),ANDROID_HOME=str(sdk),ANDROID_SDK_ROOT=str(sdk),NATIVE_TARGET='arm64-v8a',COMMIT_ID=commit,CHAQUOPY_BUILD_PYTHON=str(py),ALPHA_WHEELHOUSE=str(wheel),CMAKE=str(sdk/'cmake/3.31.6/bin/cmake'))
 env['PATH']=str(jdk/'bin')+os.pathsep+str(py.parent)+os.pathsep+env.get('PATH','')
 # Follow the existing CI's JDK21 vendor adaptation only for the build, then restore exact source.
 criteria=ROOT/'gradle/gradle-daemon-jvm.properties';original=criteria.read_bytes();local=ROOT/'local.properties';oldlocal=local.read_bytes()if local.exists()else None
 staged=[ROOT/'config/connected-alpha-test.keystore',ROOT/'TMessagesProj/src/connectedAlpha/google-services.json']
 values=list(secret.values());firebase=json.loads(__import__('base64').b64decode(secret['ALPHA_FIREBASE_JSON_B64']))
 for c in firebase.get('client',[]):values.extend(str(k.get('current_key',''))for k in c.get('api_key',[]))
 log=out/'build-redacted.log'
 try:
  stage(env);criteria.write_text('toolchainVersion=21\ntoolchainVendor=ADOPTIUM\n');local.write_text('sdk.dir='+str(sdk)+'\n')
  command=['./gradlew',':TMessagesProj:assembleConnectedAlpha','--no-daemon','--console=plain','--max-workers=2']
  with log.open('w') as f:
   proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
   for line in proc.stdout:
    safe=redact(line,values);f.write(safe);f.flush()
    if any(t in safe for t in ('BUILD SUCCESSFUL','BUILD FAILED','> Task', 'FAILURE:')):print(safe,end='',flush=True)
   if proc.wait()!=0:raise RuntimeError('Full Android build failed; inspect the redacted build log')
  apks=list((ROOT/'TMessagesProj/build/outputs/apk/connectedAlpha').rglob('*.apk'))
  if len(apks)!=1:raise ValueError('Expected exactly one full Connected Alpha APK')
  name='FlexyGram_Alpha_1286_ARM64_TEST.apk';target=out/name
  result=subprocess.run([sys.executable,str(ROOT/'tools/connected_alpha/verify_apk.py'),str(apks[0]),'--build-tools',str(sdk/'build-tools/36.0.0'),'--certificate-sha256',CERT,'--expected-version-code','1286'],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
  report=json.loads(result.stdout)
  if report['application_id']!=APP or report['elf_count']!=96:raise ValueError('Full native APK identity/integrity mismatch')
  shutil.copy2(apks[0],target);target.chmod(0o600)
  if hashlib.sha256(target.read_bytes()).hexdigest()!=report['sha256']:raise ValueError('Final handoff copy mismatch')
  report.update(commit=commit,delivery='PRIVATE_DIRECT_SIGNED_APK',filename=name,physical_install_update='NOT_TESTED',preview_physical_freeze='PENDING_OWNER_TEST',exteraless_performance_comparison='NOT_ESTABLISHED')
  (out/'FlexyGram_Alpha_1286_verificacion.json').write_text(json.dumps(report,indent=2)+'\n')
  print(json.dumps({k:report[k]for k in ['filename','sha256','certificate_sha256','application_id','version_code','elf_count','commit']},indent=2))
 finally:
  criteria.write_bytes(original)
  if oldlocal is None:local.unlink(missing_ok=True)
  else:local.write_bytes(oldlocal)
  for path in staged:path.unlink(missing_ok=True)
 return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,RuntimeError,OSError,subprocess.SubprocessError):
  print('Private Android build/verification failed. No incompatible APK is presented as an update. Inspect only the redacted local build log.',file=sys.stderr);raise SystemExit(1)
