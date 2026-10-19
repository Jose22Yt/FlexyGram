"""Inspect a newly compiled P0.4b APK; no installation or network execution.
Run only with matching APK/classes/graph/merged manifest from the same source build.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/translation_staging'))
from check_integration import inspect

def native_policy_entry(libraries):
 matches=[name for name in libraries if re.fullmatch(r'lib/arm64-v8a/libtmessages(?:\.\d+)?\.so',name)]
 assert len(matches)==1,'missing or ambiguous versioned JNI application library'
 return matches[0]

def validate(apk,aapt2,classes,graph,manifest,readelf):
 report=inspect(apk,aapt2,classes,graph,manifest)
 constants=subprocess.check_output(['javap','-constants','-classpath',str(classes),'org.telegram.messenger.BuildConfig'],text=True)
 policy=json.loads((ROOT/'gradle/variant-policy.json').read_text())['variants']['diagnostic']
 scope=hashlib.sha256((ROOT/'gradle/variant-policy.json').read_bytes()).hexdigest()+':diagnostic'
 for capability in policy['capabilities']:
  assert re.search(r'\bFLEXYGRAM_CAP_'+capability.upper()+r' = false;',constants),'unexpected compiled capability'
 assert 'FLEXYGRAM_VARIANT = "diagnostic";' in constants
 assert 'FLEXYGRAM_POLICY_SCOPE = "'+scope+'";' in constants
 assert 'APPLICATION_ID = "'+policy['applicationId']+'";' in constants
 marker=('FLEXYGRAM_POLICY:'+scope+':auth=0:transport=0:push=0:translation=0:plugins=0:restore=0').encode()
 with zipfile.ZipFile(apk) as z:
  libs=[n for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')]
  assert libs and all(n.startswith('lib/arm64-v8a/') for n in libs),'wrong ABI'
  native=z.read(native_policy_entry(libs));assert marker in native,'JNI scope/capabilities disagree with Java'
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'libtmessages.so';f.write_bytes(native)
   symbols=subprocess.check_output([str(readelf),'--dyn-syms','--wide',str(f)],text=True)
   assert 'flexygram_variant_policy' in symbols,'linked native policy export missing'
 resources=subprocess.check_output([str(aapt2),'dump','resources',str(apk)],text=True)
 for name in ['flexygram_account_type','flexygram_storage_namespace']:
  block=resources.split('string/'+name,1)[1].split('resource ',1)[0]
  assert policy['applicationId'] in block,'wrong compiled data identity'
  assert 'io.github.jose22yt.flexygram.app' not in block,'production identity in Diagnostic resource'
 report['variant_policy']={'java_jni_scope':scope,'all_capabilities_disabled':True,'native_policy_export_verified':True,'compiled_data_resources_diagnostic':True}
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['apk','aapt2','classes','graph','manifest','readelf','output']:p.add_argument('--'+n,required=True,type=Path)
 a=p.parse_args();r=validate(a.apk,a.aapt2,a.classes,a.graph,a.manifest,a.readelf)
 a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'apk_sha256':r['apk_sha256'],'variant_policy':r['variant_policy'],'installed':False,'distributed':False}))
