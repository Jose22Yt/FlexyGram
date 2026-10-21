"""Build the REVIEW-ONLY realAlpha source overlay; never edits the shared client or runs Gradle."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
TARGET=Path('TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java')
def materialize(output):
    output=output.resolve();allowed=(ROOT/'build/generated/flexygram-local-login').resolve()
    if output!=allowed:raise ValueError('FIXED_LOCAL_OVERLAY_DESTINATION_REQUIRED')
    inventory=json.loads((ROOT/'patches/native-login-pages/inventory.json').read_text())
    original=(ROOT/TARGET).read_bytes()
    if hashlib.sha256(original).hexdigest()!=inventory['target_sha256']:raise ValueError('ORIGINAL_SOURCE_CONTEXT_CHANGED')
    patches=[ROOT/'patches/native-login-wiring/0002-native-fragment-local-binding.patch',ROOT/'patches/native-login-pages/0004-native-local-pages.patch']
    for path,digest in inventory['prerequisites'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('PREREQUISITE_PATCH_CHANGED')
    with tempfile.TemporaryDirectory() as d:
        folder=Path(d);target=folder/TARGET;target.parent.mkdir(parents=True);target.write_bytes(original)
        for patch in patches:
            subprocess.run(['git','apply','--check',str(patch)],cwd=folder,check=True,capture_output=True)
            subprocess.run(['git','apply',str(patch)],cwd=folder,check=True,capture_output=True)
        result=target.read_bytes()
    if hashlib.sha256(result).hexdigest()!=inventory['overlay_sha256']:raise ValueError('OVERLAY_CONTENT_MISMATCH')
    destination=output/'java/org/telegram/ui/LoginActivity.java'
    if destination.exists() and destination.read_bytes()!=result:raise ValueError('REFUSING_DIFFERENT_EXISTING_OVERLAY')
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():destination.write_bytes(result)
    receipt={'original_sha256':hashlib.sha256(original).hexdigest(),'overlay_sha256':hashlib.sha256(result).hexdigest(),'patch_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in patches},'compilation_executed':False,'android_executed':False}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'build/generated/flexygram-local-login');args=parser.parse_args();print(json.dumps(materialize(args.output)))
