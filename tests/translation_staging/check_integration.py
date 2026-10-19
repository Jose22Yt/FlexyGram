"""Read-only P0.3g integration evidence. Never executes/installs an Android app.
No matched secret literals, certificate bytes or conversation text are emitted.
"""
from pathlib import Path
import argparse,collections,hashlib,json,os,re,struct,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/translation_runtime'))
sys.path.insert(0,str(ROOT/'tests/security'))
sys.path.insert(0,str(ROOT/'tests/translation_safety'))
from check_artifact import check
from manifest_surface import audit,check_mutations
from artifact_gate import scan

EXPECTED={'Lapp/nekogram/translator/'+name+';' for name in ['BaseTranslator','Result','MicrosoftTranslator','DeepLTranslator','Http429Exception','LanguageCodes']}

def dex_definitions(data):
 assert data[:4]==b'dex\n','not a standard DEX'
 def number(offset):return struct.unpack_from('<I',data,offset)[0]
 def string(index):
  offset=number(number(60)+4*index)
  # Skip UTF-16 length (ULEB128). Class names cannot contain an embedded NUL.
  for _ in range(5):
   byte=data[offset];offset+=1
   if not byte&128:break
  else:raise AssertionError('invalid DEX string length')
  return data[offset:data.index(0,offset)].decode('utf-8',errors='surrogatepass')
 type_offset=number(68);class_count=number(96);class_offset=number(100)
 for index in range(class_count):
  type_index=number(class_offset+32*index)
  yield string(number(type_offset+4*type_index))

def summarize_artifact(path,registry):
 result=scan(path.read_bytes(),registry)
 # Source filesystem paths remain private; identifiers and hashes are sufficient for evidence.
 return {'name':path.name,'bytes':path.stat().st_size,**result}

def inspect(apk,aapt2,classes,graph,manifest):
 registry=json.loads((ROOT/'tests/translation_safety/retired_fingerprints.json').read_text())
 result=check(apk,aapt2,classes)
 result['merged_manifest']=audit(manifest)
 result['negative_manifest_mutations']=check_mutations(manifest)
 definitions=collections.Counter()
 with zipfile.ZipFile(apk) as archive:
  for name in archive.namelist():
   if re.fullmatch(r'classes(?:\d+)?\.dex',name):definitions.update(dex_definitions(archive.read(name)))
 duplicates=sorted(name for name,count in definitions.items() if count>1)
 assert not duplicates,'duplicate DEX class definitions'
 facade={name:definitions[name] for name in sorted(EXPECTED)}
 assert all(count==1 for count in facade.values()),'missing or duplicated facade class'
 legacy=sorted(name for name in definitions if name.startswith('Lapp/nekogram/translator/') and name not in EXPECTED)
 assert not legacy,'unexpected translation AAR class remains'
 fixtures=[name for name in definitions if name.startswith(('Llab/flexygram/fixture/','Llab/flexygram/translation/'))]
 assert not fixtures,'laboratory transport leaked into APK'
 result['dex_classes']={'total':sum(definitions.values()),'duplicate_definitions':len(duplicates),'facade':facade,'unexpected_legacy_classes':legacy,'fixture_classes':fixtures}
 graphs=json.loads(graph.read_text());external={};components={}
 for scope,row in graphs.items():
  assert not any('app.nekogram.translator:translator:' in name for name in row['components'])
  assert any('translation-compat-diagnostic' in name for name in row['components'])
  components[scope]=row['components']
  for artifact in row['externalArtifacts']:
   path=Path(artifact['file']);external[(artifact['id'],str(path))]=path
 results=[]
 for (identity,_),path in sorted(external.items()):
  assert path.is_file(),'dependency artifact missing'
  results.append({'id':identity,**summarize_artifact(path,registry)})
 module=ROOT/'TMessagesProj_Modules/translation-compat-diagnostic/build/libs'
 jars=list(module.glob('*.jar'));assert len(jars)==1
 local=summarize_artifact(jars[0],registry)
 result['resolved_components']=components
 result['dependency_scans']=results
 result['source_facade_jar_scan']=local
 constants=subprocess.run(['javap','-constants','-classpath',classes,'org.telegram.messenger.BuildConfig'],check=True,capture_output=True,text=True).stdout
 assert re.search(r'\bAPP_ID = 0;',constants)
 assert 'APP_HASH = "";' in constants and 'ISOLATED_DIAGNOSTIC = true;' in constants
 result['compiled_isolation']={'api_id_zero':True,'api_hash_empty':True,'isolated_diagnostic':True}
 result['all_translation_gates_passed']=bool(result['translation_scan']['passed'] and local['passed'] and all(row['passed'] for row in results))
 result['distribution_allowed']=False
 result['limits']='Static APK, DEX, JAR, dependencies and manifest inspection. No ART, device, emulator, network provider, login, install or distribution. Clean scanner is not authorization to enable or distribute.'
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('apk',type=Path);p.add_argument('--aapt2',required=True,type=Path);p.add_argument('--classes',required=True)
 p.add_argument('--graph',required=True,type=Path);p.add_argument('--manifest',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
 args=p.parse_args();result=inspect(args.apk,args.aapt2,args.classes,args.graph,args.manifest)
 args.output.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'apk_sha256':result['apk_sha256'],'dependency_artifacts_scanned':len(result['dependency_scans']),'clean_translation_gates':result['all_translation_gates_passed'],'distribution_allowed':False}))
 raise SystemExit(0 if result['all_translation_gates_passed'] else 1)
