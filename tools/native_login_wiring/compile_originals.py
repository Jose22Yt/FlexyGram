"""Attempt unchanged complete sources. Nonzero is BLOCKED, never a compatibility PASS.
No Gradle, downloads, APK or Android execution. Supply reviewed dependency jars via --classpath.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[2]
TARGETS=['org/telegram/ui/LoginActivity.java','org/telegram/messenger/UserConfig.java','org/telegram/messenger/AccountInstance.java','org/telegram/messenger/MessagesStorage.java','org/telegram/messenger/SRPHelper.java','org/telegram/tgnet/ConnectionsManager.java','org/telegram/tgnet/TLRPC.java','org/telegram/tgnet/tl/TL_account.java']
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--classpath',required=True);parser.add_argument('--generated-source',action='append',default=[],type=Path);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True);base=ROOT/'TMessagesProj/src/main/java'
    sources=[base/path for path in TARGETS]
    for module in ['telegram-session-core','telegram-session-android','telegram-native-login','telegram-login-wiring']:
        sources+=sorted((ROOT/'TMessagesProj_Modules'/module).glob('src/*/java/**/*.java'))
    javac=Path(os.environ['JAVA_HOME'])/'bin/javac'
    command=[str(javac),'-J-Xmx1536m','-proc:none','-Xmaxerrs','60','-encoding','UTF-8','-classpath',args.classpath,'-sourcepath',os.pathsep.join(map(str,[base,*args.generated_source])),'-d',str(args.output/'classes'),*map(str,sources)]
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=180)
        log=result.stdout+result.stderr;code=result.returncode
    except subprocess.TimeoutExpired as unavailable:
        log='COMPILE_TIMEOUT_180_SECONDS\n';code=124
    (args.output/'javac.log').write_text(log)
    receipt={'status':'COMPILED' if code==0 else 'BLOCKED','returncode':code,'command':command,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'android_runtime':False,'projected_tl':False,'classpath':args.classpath}
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status']);return code
if __name__=='__main__':raise SystemExit(main())
