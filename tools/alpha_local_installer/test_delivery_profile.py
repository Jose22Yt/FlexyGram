"""Cross-language profile checks; no private identities or application credentials."""
from pathlib import Path
import re
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent

class SignatureHome2Profile(unittest.TestCase):
    def test_native_and_java_pins_match_exact_delivery(self):
        native = (ROOT/'internal/delivery/delivery.go').read_text()
        java = (ROOT/'android/src/io/github/jose22yt/flexygram/delivery/Contract.java').read_text()
        for go_name, java_name in [('APKHash','HASH'),('CipherHash','CIPHER_HASH'),('Commit','COMMIT'),('CertificateSHA256','CERTIFICATE')]:
            value = re.search(r'const '+go_name+r' = "([^"]+)"', native)[1]
            self.assertIn('String '+java_name+' = "'+value+'"', java)
            self.assertRegex(value, r'^[0-9a-f]{40}$' if go_name == 'Commit' else r'^[0-9a-f]{64}$')
        self.assertIn('r.VersionCode != 1268', native)
        self.assertIn('p.getLongVersionCode() != 1268', java)
        self.assertIn('r.getLong("version_code") != 1268', java)
        self.assertIn('cb2c98234aa7e88550853d54132e52d629b2674f', native)

    def test_offline_manifest_and_local_selection(self):
        a='{http://schemas.android.com/apk/res/android}'
        root=ET.parse(ROOT/'android/AndroidManifest.xml').getroot()
        self.assertEqual(root.get('package'),'io.github.jose22yt.flexygram.delivery.alpha2.home2v1268')
        self.assertEqual([p.get(a+'name') for p in root.findall('uses-permission')],['android.permission.REQUEST_INSTALL_PACKAGES'])
        self.assertEqual(root.find('application').get(a+'allowBackup'),'false')
        activity=(ROOT/'android/src/io/github/jose22yt/flexygram/delivery/MainActivity.java').read_text()
        self.assertIn('Intent.EXTRA_LOCAL_ONLY, true',activity)
        self.assertIn('FlexyGram-SignatureHome2-ARM64.tar.age',activity)
        self.assertNotIn('takePersistableUriPermission',activity)
        self.assertIn('FLAG_SECURE',activity)
        self.assertNotIn('getMessage()',activity)
        self.assertNotIn('printStackTrace',activity)

    def test_jni_provider_and_workflow_refer_to_same_profile(self):
        a='{http://schemas.android.com/apk/res/android}'
        root=ET.parse(ROOT/'android/AndroidManifest.xml').getroot()
        package=root.get('package')
        bridge=(ROOT/'android/bridge.c').read_text()
        self.assertIn('Java_'+package.replace('.','_')+'_MainActivity_decryptNative(',bridge)
        provider=root.find('application/provider').get(a+'authorities')
        java=(ROOT/'android/src/io/github/jose22yt/flexygram/delivery/VerifiedApkProvider.java').read_text()
        self.assertIn('content://'+provider+'/verified/FlexyGram-Alpha-arm64.apk',java)
        workflow=(ROOT.parents[1]/'.github/workflows/alpha-local-installer.yml').read_text()
        self.assertIn('ref: cb2c98234aa7e88550853d54132e52d629b2674f',workflow)
        self.assertIn('name: FlexyGram-SignatureHome2-Installer',workflow)
        self.assertIn('FlexyGram-SignatureHome2-Instalador.apk',workflow)

if __name__ == '__main__': unittest.main()
