"""Synthetic gate tests, not evidence of an Android build or runtime."""
import importlib.util,tempfile,unittest,zipfile
from unittest.mock import patch
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('alpha_review',ROOT/'tools/real_alpha/review_apk.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);A=r.A
def fixture():
    root=ET.Element('manifest',{'package':r.PACKAGE})
    ET.SubElement(root,'uses-sdk',{A+'minSdkVersion':'24',A+'targetSdkVersion':'36'})
    name=r.PACKAGE+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
    ET.SubElement(root,'permission',{A+'name':name,A+'protectionLevel':'signature'})
    for n in ['android.permission.ACCESS_NETWORK_STATE',name]:ET.SubElement(root,'uses-permission',{A+'name':n})
    app=ET.SubElement(root,'application',{A+'name':'org.telegram.messenger.ApplicationLoader',A+'debuggable':'true',A+'allowBackup':'false',A+'restoreAnyVersion':'false',A+'fullBackupContent':'false',A+'usesCleartextTraffic':'false'})
    act=ET.SubElement(app,'activity',{A+'name':r.ENTRY,A+'exported':'true'})
    intent=ET.SubElement(act,'intent-filter')
    ET.SubElement(intent,'action',{A+'name':'android.intent.action.MAIN'})
    ET.SubElement(intent,'category',{A+'name':'android.intent.category.LAUNCHER'})
    ET.SubElement(app,'provider',{A+'name':'ru.noties.jlatexmath.JLatexMathInitProvider',A+'authorities':r.PACKAGE+'.jlatexmathinitprovider',A+'exported':'false'})
    for n,v in [('firebase_messaging_auto_init_enabled','false'),('firebase_analytics_collection_deactivated','true'),('firebase_crashlytics_collection_enabled','false')]:ET.SubElement(app,'meta-data',{A+'name':n,A+'value':v})
    return root
class ReviewTests(unittest.TestCase):
    def test_host_debugpy_asset_is_separate_and_pinned_not_arm64(self):
        host={'machine':'EM_X86_64','path':'fixture.apk!assets/chaquopy/requirements-common.imy!debugpy/_vendored/pydevd/pydevd_attach_to_process/attach_linux_amd64.so','sha256':'8fafec366c6a3b38d3429c7a9ad9957fd029f170eac9fd37bdecbbbebb3e9441'}
        arm=[{'machine':'EM_AARCH64'} for _ in range(96)]
        r.check_native_inventory({'libraries':arm+[host]})
        for rows in [arm,arm[:-1]+[host],arm+[dict(host,sha256='0'*64)],arm+[dict(host,path='fixture.apk!lib/x86_64/foreign.so')],arm+[dict(host,machine='EM_ARM')]]:
            with self.subTest(rows=rows[-1]),self.assertRaises(ValueError):r.check_native_inventory({'libraries':rows})
    def test_external_tool_modified_utf8_preserves_ascii_structure(self):
        import sys
        result=r.command([sys.executable,'-c',"import sys;sys.stdout.buffer.write(b'Class descriptor: ASCII\\n\\xc0\\x80')"])
        self.assertIn('Class descriptor: ASCII',result)
        self.assertIn(r'\xc0\x80',result)
    def test_source_compatibility_exception_is_glyph_only_and_legacy_gates_unchanged(self):
        tools='{http://schemas.android.com/tools}'
        manifest=ET.parse(ROOT/'TMessagesProj/src/realAlpha/AndroidManifest.xml').getroot()
        self.assertEqual([x.get(tools+'overrideLibrary') for x in manifest.findall('uses-sdk')],['com.nothing.thirdparty'])
        self.assertTrue(any('com.nothing.thirdparty' in x.get(tools+'overrideLibrary','') for x in ET.parse(ROOT/'TMessagesProj/src/betaDevelopment/AndroidManifest.xml').getroot().findall('uses-sdk')))
        import subprocess
        for path in ['tools/beta_development/review_apk.py','TMessagesProj/src/diagnostic/AndroidManifest.xml','TMessagesProj/src/betaDevelopment/AndroidManifest.xml','gradle/variant-policy.json','gradle/beta-development.json','gradle/real-alpha.json']:
            self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT))
    def test_exact_closed_fixture(self):self.assertEqual(r.validate_manifest(fixture())['package'],r.PACKAGE)
    def test_other_identities_rejected(self):
        for name in ['io.github.jose22yt.flexygram.beta.development','io.github.jose22yt.flexygram.diagnostic','com.exteraless.app']:
            with self.subTest(name=name),self.assertRaises(ValueError):
                root=fixture();root.set('package',name);r.validate_manifest(root)
    def test_internet_and_duplicate_permissions_rejected(self):
        for n in ['android.permission.INTERNET','android.permission.ACCESS_NETWORK_STATE']:
            with self.subTest(name=n),self.assertRaises(ValueError):
                root=fixture();ET.SubElement(root,'uses-permission',{A+'name':n});r.validate_manifest(root)
    def test_extra_components_rejected(self):
        for kind in ['activity','activity-alias','provider','receiver','service']:
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                root=fixture();ET.SubElement(root.find('application'),kind,{A+'name':'unexpected.Component',A+'enabled':'false',A+'exported':'false'});r.validate_manifest(root)
    def test_restore_exposure_and_external_collection_rejected(self):
        for target,attr,value in [('application','allowBackup','true'),('application','restoreAnyVersion','true'),('application','fullBackupContent','true'),('application/provider','exported','true'),('application/provider','authorities','com.exteraless.app.provider'),('application/meta-data','value','true')]:
            with self.subTest(target=target,attribute=attr),self.assertRaises(ValueError):
                root=fixture();root.find(target).set(A+attr,value);r.validate_manifest(root)
    def test_dex_native_factory_must_be_in_exact_class_and_method(self):
        listing="""Class #0
  Class descriptor : 'Lorg/telegram/ui/realalpha/RealAlphaActivity;'
  Superclass : 'Lorg/telegram/ui/LaunchActivity;'
    #0
      name : 'getClientNotActivatedFragment'
      access : 0x0004
      new-instance v0, Lorg/telegram/ui/DialogsActivity;
      invoke-direct {v0,v1}, Lorg/telegram/ui/DialogsActivity;.<init>
    #1
      name : 'otherMethod'
Class #1
  Class descriptor : 'Lorg/telegram/ui/LaunchActivity;'
      name : 'onBackPressed'
      invoke-interface registerOnBackInvokedCallback
      invoke-interface unregisterOnBackInvokedCallback
      check-cast OnBackAnimationCallback
Class #2
  Class descriptor : 'Lorg/telegram/ui/DialogsActivity;'
"""
        with tempfile.TemporaryDirectory() as folder:
            apk=Path(folder)/'synthetic.apk'
            with zipfile.ZipFile(apk,'w') as z:z.writestr('classes.dex',b'synthetic fixture')
            with patch.object(r,'command',return_value=listing):r.verify_dex_linkage(apk,Path('synthetic-dexdump'))
            mutations=[listing.replace('Lorg/telegram/ui/LaunchActivity;','Lorg/telegram/ui/beta/BetaPreviewActivity;'),listing.replace("'getClientNotActivatedFragment'","'unrelatedFactory'"),listing.replace('      new-instance',"    #1\n      name : 'unrelatedFactory'\n      new-instance"),listing+listing,listing.replace("Class descriptor : 'Lorg/telegram/ui/DialogsActivity;'","Class descriptor : 'Lsynthetic/Missing;'"),listing+"\nClass #3\n  Class descriptor : 'Lorg/telegram/ui/realalpha/RealAlphaBack;'",listing.replace("name : 'otherMethod'","name : 'onBackPressed'"),listing.replace("name : 'otherMethod'","name : 'onDestroy'"),listing.replace('unregisterOnBackInvokedCallback','removedUnregister'),listing.replace('check-cast OnBackAnimationCallback','removedPredictiveCallback')]
            mutations.append(listing.replace("      name : 'onBackPressed'", "      name : 'onBackPressed'\n      invoke-static Lorg/telegram/messenger/FingerprintController;.checkKeyReady:()V"))
            for m in mutations:
                with self.subTest(mutation=m),patch.object(r,'command',return_value=m),self.assertRaises(ValueError):r.verify_dex_linkage(apk,Path('synthetic-dexdump'))
    def test_biometric_dex_guard_requires_constant_identity_and_forward_skip(self):
        block='''|0100: const-string v0, "realAlpha"
|0102: invoke-virtual {v0, v0}, Ljava/lang/String;.equals:(Ljava/lang/Object;)Z
|0105: move-result v0
|0106: if-nez v0, 010b // +0005
|0108: invoke-static {}, Lorg/telegram/messenger/FingerprintController;.checkKeyReady:()V
'''
        r.verify_offline_biometric_guard(block)
        for bad in [block.replace('realAlpha','diagnostic'),block.replace('if-nez','if-eqz'),block.replace('010b','0100'),block.replace('move-result v0','move-result v1'),block.replace('|0102:', '|0101: move-object v0, v1\n|0102:')]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):r.verify_offline_biometric_guard(bad)
if __name__=='__main__':unittest.main()
