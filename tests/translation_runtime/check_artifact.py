"""Read-only checks of the built diagnostic APK. Never installs/runs an app.
Exit 1 is expected while inherited translation keys remain; no matched value is printed.
"""
import argparse, hashlib, json, re, struct, subprocess, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/security'))
sys.path.insert(0,str(ROOT/'tests/translation_safety'))
from artifact_gate import scan, CLIENT, CLIENT16
from manifest_surface import audit_binary


def check(apk,aapt2,classes=None):
    raw=apk.read_bytes()
    registry=json.loads((ROOT/'tests/translation_safety/retired_fingerprints.json').read_text())
    findings=scan(raw,registry,require_apk=True)
    manifest=audit_binary(apk,aapt2)
    known=set(registry['retired_key_sha256']);found=set();native=[];policy=False
    with zipfile.ZipFile(apk) as z:
        assert z.testzip() is None
        for name in z.namelist():
            if re.fullmatch(r'classes(?:\d+)?\.dex',name):
                data=z.read(name)
                policy|=b'Ltw/nekomimi/nekogram/translate/TranslationServicesPolicy;' in data
                for pattern in [CLIENT,CLIENT16]:
                    for m in pattern.finditer(data):
                        digest=hashlib.sha256(m[0].replace(b'\x00',b'')).hexdigest()
                        if digest in known:found.add(digest)
            if name.startswith('lib/') and name.endswith('.so'):
                data=z.read(name)
                assert name.startswith('lib/arm64-v8a/') and data[:4]==b'\x7fELF' and data[4]==2
                assert struct.unpack_from('<H',data,18)[0]==183
                native.append(name)
    assert policy,'Policy class missing from DEX'
    assert native,'No installed native libraries'
    compiled={}
    if classes:
        classes_to_check={
          'tw.nekomimi.nekogram.translate.source.GoogleTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.GoogleAppTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.GoogleCloudTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.LLMTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.MicrosoftTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.RealMicrosoftTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.DeepLTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.YandexTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.LingoTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.TelegramAPITranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.TranSmartTranslator':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.fallback.GoogleTranslatorNeko':'requireRoute',
          'tw.nekomimi.nekogram.translate.source.fallback.DeepLTranslatorNeko':'requireRoute',
          'tw.nekomimi.nekogram.translate.Translator$Companion':'requireProvider',
          'tw.nekomimi.nekogram.translate.Translator$Companion$translatePoll$1':'requireProvider',
          'tw.nekomimi.nekogram.translate.Translator$Companion$translateWithContext$1':'requireProvider',
          'tw.nekomimi.nekogram.parts.MessageTransKt':'requireProvider',
        }
        for cls,method in classes_to_check.items():
            text=subprocess.run(['javap','-c','-p','-classpath',classes,cls],check=True,capture_output=True,text=True).stdout
            count=text.count('TranslationServicesPolicy.'+method)
            assert count>0,cls
            compiled[cls]={'policy_invocations':count}
    return {'apk_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
            'manifest':manifest,'policy_class_present_in_dex':policy,
            'installed_aarch64_libraries':native,'zip_crc':'passed',
            'known_unique_retired_keys_in_dex':len(found),'translation_scan':findings,
            'compiled_class_policy_checks':compiled,
            'distribution_allowed':False,
            'limits':'Static APK/class inspection only; no ART/emulator, installation, login, real provider or traffic test.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('apk',type=Path);p.add_argument('--aapt2',required=True,type=Path)
    p.add_argument('--classes',help='Compiled Kotlin and Java class directories, joined by OS path separator')
    args=p.parse_args();result=check(args.apk,args.aapt2,args.classes)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['translation_scan']['passed'] else 1)
