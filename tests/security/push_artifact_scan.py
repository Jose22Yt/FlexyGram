"""Directed scanner; counts only. Not universal secret certification."""
import io,json,re,sys,zipfile,hashlib
from pathlib import Path
CLIENT_KEY=re.compile(rb'AIza[A-Za-z0-9_-]{35}')
CLIENT_KEY_UTF16=re.compile(rb'A\x00I\x00z\x00a\x00(?:[A-Za-z0-9_-]\x00){35}')
def scan_bytes(payload,forbidden):
    needles=[v.encode(enc) for v in forbidden if v for enc in ('utf-8','utf-16le')]
    result={'zip_entries':0,'nested_archives':0,'forbidden_value_hits':0,'client_key_shaped_hits':0,'embedded_google_services_json':0}
    def inspect(data,depth):
        result['forbidden_value_hits']+=sum(n in data for n in needles)
        result['client_key_shaped_hits']+=len(CLIENT_KEY.findall(data))+len(CLIENT_KEY_UTF16.findall(data))
        if depth<5 and zipfile.is_zipfile(io.BytesIO(data)):
            if depth:result['nested_archives']+=1
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for entry in z.infolist():
                    if entry.is_dir():continue
                    result['zip_entries']+=1
                    if Path(entry.filename).name=='google-services.json':result['embedded_google_services_json']+=1
                    inspect(z.read(entry),depth+1)
    inspect(payload,0);result['passed']=not any(result[k] for k in ['forbidden_value_hits','client_key_shaped_hits','embedded_google_services_json']);result['sha256']=hashlib.sha256(payload).hexdigest();return result
if __name__=='__main__':
    values=json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv)>2 else []
    result=scan_bytes(Path(sys.argv[1]).read_bytes(),values);print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
