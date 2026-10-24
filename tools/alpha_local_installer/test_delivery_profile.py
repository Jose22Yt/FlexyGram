"""Fail-closed delivery profile and actual Java/native/manifest identity agreement."""
import re,unittest
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parent
class DeliveryProfile(unittest.TestCase):
 def test_pins_are_all_blocked_or_exact_and_match_java(self):
  native=(ROOT/'internal/delivery/delivery.go').read_text();java=(ROOT/'android/src/io/github/jose22yt/flexygram/delivery/Contract.java').read_text()
  pins=dict(re.findall(r'const (APKHash|CipherHash|Commit) = "([^"]*)"',native));jp=dict(re.findall(r'static final String (HASH|CIPHER_HASH|COMMIT) = "([^"]*)"',java))
  for n,j in [('APKHash','HASH'),('CipherHash','CIPHER_HASH'),('Commit','COMMIT')]:self.assertEqual(pins[n],jp[j])
  if any(pins.values()):
   for n,size in [('APKHash',64),('CipherHash',64),('Commit',40)]:self.assertRegex(pins[n],r'^[0-9a-f]{'+str(size)+'}$')
  else:self.assertEqual(pins,{'APKHash':'','CipherHash':'','Commit':''})
  workflow=(ROOT.parents[1]/'.github/workflows/alpha-local-installer.yml').read_text()
  if pins['Commit']:self.assertIn('ref: '+pins['Commit'],workflow)
  self.assertGreaterEqual(workflow.count("if: steps.profile.outputs.ready == 'true'"),5)
  self.assertIn('FlexyGram-Alpha1271-Instalador.apk',workflow)
  self.assertIn('r.VersionCode != 1271',native);self.assertIn('p.getLongVersionCode() != 1271',java)
  original='c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c'
  self.assertIn(original,java);self.assertIn(original,native)
 def test_offline_manifest_jni_and_provider_agree(self):
  a='{http://schemas.android.com/apk/res/android}';manifest=ET.parse(ROOT/'android/AndroidManifest.xml').getroot();package='io.github.jose22yt.flexygram.delivery.alpha1271'
  self.assertEqual(manifest.get('package'),package)
  self.assertEqual([x.get(a+'name') for x in manifest.findall('uses-permission')],['android.permission.REQUEST_INSTALL_PACKAGES'])
  self.assertEqual(manifest.find('application/provider').get(a+'authorities'),package+'.files')
  self.assertEqual(manifest.find('application/provider').get(a+'exported'),'false')
  self.assertIn('Java_'+package.replace('.','_')+'_MainActivity_decryptNative',(ROOT/'android/bridge.c').read_text())
