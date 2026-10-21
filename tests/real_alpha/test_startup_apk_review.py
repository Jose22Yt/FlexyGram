"""Distinct identity gate: no weakening of the existing unsigned APK verifier."""
import copy,importlib.util,sys,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/real_alpha'))
import review_startup_apk as gate
A=gate.A

def fixture():
 root=ET.Element('manifest',package=gate.PACKAGE)
 ET.SubElement(root,'uses-sdk',{A+'minSdkVersion':'24',A+'targetSdkVersion':'36'})
 for name in ['android.permission.ACCESS_NETWORK_STATE',gate.PACKAGE+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION']:ET.SubElement(root,'uses-permission',{A+'name':name})
 ET.SubElement(root,'permission',{A+'name':gate.PACKAGE+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION',A+'protectionLevel':'signature'})
 app=ET.SubElement(root,'application',{A+'name':gate.APP,A+'debuggable':'true',**{A+n:'false' for n in ['allowBackup','restoreAnyVersion','fullBackupContent','usesCleartextTraffic']}})
 report=ET.SubElement(app,'activity',{A+'name':gate.REPORT,A+'exported':'true'})
 i=ET.SubElement(report,'intent-filter');ET.SubElement(i,'action',{A+'name':'android.intent.action.MAIN'});ET.SubElement(i,'category',{A+'name':'android.intent.category.LAUNCHER'})
 ET.SubElement(app,'activity',{A+'name':gate.PROBE,A+'exported':'false',A+'process':':startup_probe'})
 ET.SubElement(app,'provider',{A+'name':'ru.noties.jlatexmath.JLatexMathInitProvider',A+'exported':'false',A+'process':':startup_probe',A+'authorities':gate.PACKAGE+'.jlatexmathinitprovider'})
 for name,value in [('firebase_messaging_auto_init_enabled','false'),('firebase_analytics_collection_deactivated','true'),('firebase_crashlytics_collection_enabled','false')]:ET.SubElement(app,'meta-data',{A+'name':name,A+'value':value})
 return root
class StartupApkReviewTests(unittest.TestCase):
 def rejected(self,mutate):
  root=fixture();mutate(root)
  with self.assertRaises(ValueError):gate.validate(root)
 def test_binary_namespace_uri_and_signature_permission(self):
  from unittest.mock import patch
  dump='E: manifest\n  A: package="'+gate.PACKAGE+'"\n  E: uses-sdk\n    A: http://schemas.android.com/apk/res/android:minSdkVersion(0x0101020c)=0x18\n  E: permission\n    A: http://schemas.android.com/apk/res/android:protectionLevel(0x01010009)=0x2\n'
  with patch.object(gate.base,'command',return_value=dump):root=gate.binary_root(Path('unused.apk'),Path('unused-aapt2'))
  self.assertEqual(root.find('uses-sdk').get(A+'minSdkVersion'),'0x18')
  self.assertEqual(root.find('permission').get(A+'protectionLevel'),'signature')
 def test_exact_diagnostic_identity(self):self.assertEqual(gate.validate(fixture())['package'],gate.PACKAGE)
 def test_reject_original_identity(self):self.rejected(lambda r:r.set('package','io.github.jose22yt.flexygram.realalpha'))
 def test_reject_internet(self):self.rejected(lambda r:ET.SubElement(r,'uses-permission',{A+'name':'android.permission.INTERNET'}))
 def test_reject_probe_export(self):self.rejected(lambda r:r.find('application').findall('activity')[1].set(A+'exported','true'))
 def test_reject_report_in_probe_process(self):self.rejected(lambda r:r.find('application/activity').set(A+'process',':startup_probe'))
 def test_reject_provider_in_report_process(self):self.rejected(lambda r:r.find('application/provider').attrib.pop(A+'process'))
 def test_reject_extra_service(self):self.rejected(lambda r:ET.SubElement(r.find('application'),'service',{A+'name':'external.Service'}))
 def test_reject_restore(self):self.rejected(lambda r:r.find('application').set(A+'allowBackup','true'))
 def test_reject_normal_permission(self):self.rejected(lambda r:r.find('permission').set(A+'protectionLevel','normal'))
