"""Read class references only, never execute or print bytecode strings/credentials."""
from pathlib import Path
import struct,zipfile,json,sys,hashlib,re,subprocess

def references(data):
 assert data[:4]==b'\xca\xfe\xba\xbe'
 count=struct.unpack_from('>H',data,8)[0];pos=10;pool={};i=1
 while i<count:
  tag=data[pos];pos+=1
  if tag==1:
   n=struct.unpack_from('>H',data,pos)[0];pos+=2;pool[i]=data[pos:pos+n].decode('utf-8','replace');pos+=n
  elif tag in [7,8,16,19,20]:
   val=struct.unpack_from('>H',data,pos)[0];pos+=2
   if tag==7:pool[i]=('class',val)
  elif tag in [3,4,9,10,11,12,17,18]:pos+=4
  elif tag in [5,6]:pos+=8;i+=1
  elif tag==15:pos+=3
  else:raise ValueError('Unsupported constant pool tag')
  i+=1
 return sorted({pool[v[1]] for v in pool.values() if isinstance(v,tuple) and v[0]=='class'})

def inventory(jar):
 with zipfile.ZipFile(jar) as z:
  graph={n[:-6]:references(z.read(n)) for n in z.namelist() if n.endswith('.class')}
 roots=['app/nekogram/translator/MicrosoftTranslator','app/nekogram/translator/DeepLTranslator']
 closures={}
 for root in roots:
  seen=set();todo=[root]
  while todo:
   cls=todo.pop()
   if cls in seen:continue
   seen.add(cls);todo.extend(r for r in graph.get(cls,[]) if r in graph and r not in seen)
  closures[root]=sorted(seen)
 return {'classes_jar_sha256':hashlib.sha256(Path(jar).read_bytes()).hexdigest(),
         'internal_class_references':{k:[r for r in v if r in graph] for k,v in graph.items()},
         'provider_reference_closures':closures,
         'limits':'Constant-pool overapproximation, not reachability/initialization proof; reflection and string descriptors need separate review.'}
def languages(jar):
 result={}
 for cls in ['MicrosoftTranslator','DeepLTranslator']:
  text=subprocess.run(['javap','-c','-p','-classpath',str(jar),'app.nekogram.translator.'+cls],capture_output=True,text=True,check=True).stdout
  constructor=text.split('public app.nekogram.translator.'+cls+'();',1)[1].split('\n  public ',1)[0]
  values=re.findall(r'// String ([^\n]+)',constructor)
  # Numeric regions are valid (e.g. es-419); never silently discard a literal.
  if not values or not all(re.fullmatch('[a-z]{2,3}(?:-[A-Za-z0-9]+)?',v) for v in values):
   raise ValueError('Unreviewed constructor literal; values withheld')
  result[cls]={'constructor_languages':values,'count':len(values),
               'constructor_method_references':re.findall(r'// (?:InterfaceMethod|Method) ([^\n]+)',constructor),
               'all_constructor_string_literals_matched':True}
 return result
if __name__=='__main__':
 print(json.dumps(languages(sys.argv[1]) if '--languages' in sys.argv[2:] else inventory(sys.argv[1]),indent=2))
