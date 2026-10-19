"""Standalone test APK build. Never invokes Gradle/JNI/client build or creates keys."""
from pathlib import Path
import argparse,base64,hashlib,json,os,re,shutil,subprocess,zipfile
from contract import HERE,ROOT,digest,load_contract,require

def run(args,**kw):
    p=subprocess.run(list(map(str,args)),capture_output=True,**kw)
    require(p.returncode==0,'Laboratory build tool failed: '+Path(str(args[0])).name+'\n'+p.stderr.decode(errors='replace')[:4000])
    return p.stdout

def build(android_jar,tools,output,keystore=None,alias=None):
    c=load_contract();require(not output.exists(),'Use a new private build directory')
    require(re.search(r'^Pkg.Revision\s*=\s*36\.0\.0\s*$',(tools/'source.properties').read_text(),re.M),'Build Tools36.0.0 required')
    props=(android_jar.parent/'source.properties').read_text();require(re.search(r'AndroidVersion.ApiLevel\s*=\s*37\b',props),'Compile SDK37 required')
    output.mkdir(parents=True,mode=0o700);classes=output/'classes';dex=output/'dex';classes.mkdir();dex.mkdir()
    java=HERE/'java/io/github/jose22yt/flexygram/lab/LabInstrumentation.java'
    javac=Path(os.environ.get('JAVA_HOME','/usr'))/'bin/javac';require(javac.is_file(),'javac unavailable')
    run([javac,'-encoding','UTF-8','-source','8','-target','8','-classpath',android_jar,'-d',classes,java])
    run([tools/'d8','--min-api','24','--lib',android_jar,'--output',dex,*sorted(classes.rglob('*.class'))])
    linked=output/'linked.apk';run([tools/'aapt2','link','-I',android_jar,'--manifest',HERE/'AndroidManifest.xml','--min-sdk-version','24','--target-sdk-version','36','-o',linked])
    assets={'contract.json':(HERE/'contract.json').read_bytes(),'probe.py':(HERE/'assets/probe.py').read_bytes(),'runtime_cases.py':(ROOT/c['runtime_cases_path']).read_bytes(),'font.ttf':(ROOT/c['font_path']).read_bytes(),'font-LICENSE.txt':(ROOT/c['font_license_path']).read_bytes()}
    with zipfile.ZipFile(linked,'a',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('classes.dex',(dex/'classes.dex').read_bytes())
        for name,data in sorted(assets.items()):z.writestr('assets/'+name,data)
    apk=output/'flexygram-lab-unsigned.apk';run([tools/'zipalign','-P','16','-f','4',linked,apk])
    manifest=run([tools/'aapt2','dump','xmltree','--file','AndroidManifest.xml',apk]).decode()
    require('uses-permission' not in manifest and c['target_package'] in manifest and c['runner_class'] in manifest,'Test APK manifest isolation failed')
    (output/'manifest.log').write_text(manifest)
    signed=False
    if keystore:
        require(alias and os.environ.get('FLEXYGRAM_LAB_STORE_PASSWORD') and os.environ.get('FLEXYGRAM_LAB_KEY_PASSWORD'),'Private diagnostic signing configuration incomplete')
        public=run([Path(os.environ.get('JAVA_HOME','/usr'))/'bin/keytool','-exportcert','-keystore',keystore,'-alias',alias,'-storepass:env','FLEXYGRAM_LAB_STORE_PASSWORD'])
        require(hashlib.sha256(public).hexdigest()==c['certificate_sha256'],'Signing key is not the reviewed diagnostic lab key')
        signed_apk=output/'flexygram-lab-signed.apk'
        run([tools/'apksigner','sign','--ks',keystore,'--ks-key-alias',alias,'--ks-pass','env:FLEXYGRAM_LAB_STORE_PASSWORD','--key-pass','env:FLEXYGRAM_LAB_KEY_PASSWORD','--out',signed_apk,apk])
        text=run([tools/'apksigner','verify','--verbose','--print-certs',signed_apk]).decode()
        require('certificate SHA-256 digest: '+c['certificate_sha256'] in text,'Runner certificate mismatch')
        (output/'signature.log').write_text(text);apk=signed_apk;signed=True
    with zipfile.ZipFile(apk) as z:
        require(z.testzip() is None and not any(n.startswith('lib/') for n in z.namelist()),'Runner must not contain substitute native libraries')
    hashes={str(p.relative_to(ROOT)):digest(p) for p in [java,HERE/'AndroidManifest.xml',HERE/'assets/probe.py',HERE/'contract.json',ROOT/c['runtime_cases_path']]}
    report={'schema':1,'status':'BUILT_SIGNED_NOT_RUN' if signed else 'BUILT_UNSIGNED_NOT_INSTALLABLE','apk_sha256':digest(apk),'apk_filename':apk.name,'signed_with_reviewed_lab_key':signed,'source_hashes':hashes,'assets':{n:hashlib.sha256(b).hexdigest() for n,b in assets.items()},'reviewed_target_sha256':c['apk_sha256'],'compile_sdk':37,'min_sdk':24,'target_sdk':36,'permissions':[],'contains_client_or_native_code':False,'android_execution':False}
    (output/'build-receipt.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--android-jar',required=True,type=Path);p.add_argument('--build-tools',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--keystore',type=Path);p.add_argument('--alias')
    a=p.parse_args();print(json.dumps(build(a.android_jar,a.build_tools,a.output,a.keystore,a.alias),indent=2))
