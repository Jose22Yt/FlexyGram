#!/usr/bin/env python3
"""Real AAPT2 resource checks; isolated link probe is NOT the app merged manifest/APK."""
import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

from preflight_sdk import normalize_platform, properties

ROOT = Path(__file__).resolve().parents[2]
A = '{http://schemas.android.com/apk/res/android}'
APP = 'io.github.jose22yt.flexygram.alpha'


def check_resource_text(path):
    root = ET.parse(path).getroot()
    if (root.text or '').strip() or any((child.tail or '').strip() for child in root):
        raise ValueError('Unexpected text outside resource elements: ' + str(path))


def probe_manifest(root=ROOT):
    """Select actual provider/backup declarations; this is intentionally NOT a full merge."""
    actual = ET.parse(root/'TMessagesProj/src/main/AndroidManifest.xml').getroot()
    source = actual.find('application')
    gradle = (root/'build.gradle').read_text()
    if not re.search(r'\bcompileSdk\s*=\s*37\b', gradle) or not re.search(r'\btargetSdk\s*=\s*36\b', gradle):
        raise ValueError('Review resource probe SDK contract after changing compile/target SDK')
    if "variant.buildType == 'connectedAlpha' ? '"+APP+"'" not in (root/'TMessagesProj/build.gradle').read_text():
        raise ValueError('Unexpected application identity')
    manifest = ET.Element('manifest', {'package': APP})
    ET.SubElement(manifest, 'uses-sdk', {A+'minSdkVersion': '24', A+'targetSdkVersion': '36'})
    attrs = {key: value for key, value in source.attrib.items() if key in {
        A+'name', A+'label', A+'allowBackup', A+'restoreAnyVersion', A+'fullBackupContent',
        A+'dataExtractionRules', A+'enableOnBackInvokedCallback'}}
    app = ET.SubElement(manifest, 'application', attrs)
    providers = [p for p in source.findall('provider') if p.get(A+'authorities') == '${applicationId}.provider']
    if len(providers) != 1:
        raise ValueError('Expected one independent FileProvider')
    provider = copy.deepcopy(providers[0])
    provider.set(A+'authorities', APP+'.provider')
    app.append(provider)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'build/connected-alpha-resources')
    args = parser.parse_args()
    platform = args.sdk_root/'platforms/android-37.0'
    normalize_platform(platform)
    bt = args.sdk_root/'build-tools/36.0.0'
    if properties(bt/'source.properties').get('Pkg.Revision') != '36.0.0':
        raise ValueError('Expected original Android build-tools 36.0.0')
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    aapt = str(bt/'aapt2')

    def run(name, *command):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        (output/(name+'.log')).write_text(result.stdout)
        if result.returncode:
            raise ValueError(name + ' failed; inspect local log: ' + str(output/(name+'.log')))
        return result.stdout

    main_res = ROOT/'TMessagesProj/src/main/res'
    for path in main_res.glob('values*/*.xml'):
        check_resource_text(path)
    # Original Telegram resources use non-positional formatting. Do not rewrite
    # translations or disable build security gates to suppress those warnings.
    run('compile-main', aapt, 'compile', '--legacy', '--dir', str(main_res), '-o', str(output/'main.zip'))
    alpha = ROOT/'TMessagesProj/src/connectedAlpha/res'
    run('compile-alpha-strict', aapt, 'compile', '--dir', str(alpha), '-o', str(output/'alpha.zip'))
    # A small resource-only container proves the overlay is selected and its
    # binary XML is loadable by AAPT2 against API 37, without private Firebase.
    # It contains no application classes, JNI, credentials or signature.
    probe = output/'probe-res/xml'
    probe.mkdir(parents=True, exist_ok=True)
    for name in ('provider_paths.xml', 'connected_alpha_extraction_rules.xml'):
        shutil.copyfile(main_res/'xml'/name, probe/name)
    manifest = output/'resource-probe-manifest.xml'
    ET.register_namespace('android', A[1:-1])
    ET.ElementTree(probe_manifest()).write(manifest, encoding='utf-8', xml_declaration=True)
    run('compile-probe', aapt, 'compile', '--dir', str(probe.parent), '-o', str(output/'probe.zip'))
    container = output/'resource-probe.ap_'
    run('link-probe', aapt, 'link', '-I', str(platform/'android.jar'), '--manifest', str(manifest),
        '--auto-add-overlay', str(output/'probe.zip'), '-R', str(output/'alpha.zip'), '-o', str(container))
    xml = run('provider-binary', aapt, 'dump', 'xmltree', str(container), '--file', 'res/xml/provider_paths.xml')
    if 'saved-attachments' not in xml or 'Saved Attachments/' not in xml:
        raise ValueError('Linked resource did not select the Alpha FileProvider overlay')
    binary_manifest = run('manifest-probe-binary', aapt, 'dump', 'xmltree', str(container), '--file', 'AndroidManifest.xml')
    if APP+'.provider' not in binary_manifest:
        raise ValueError('Probe provider identity differs from Alpha')
    print(json.dumps({'status': 'PASS_RESOURCES_AND_ISOLATED_LINK_ONLY',
                      'main_compile': 'PASS_LEGACY_FORMAT_WARNINGS', 'alpha_compile': 'PASS_STRICT',
                      'api': 37, 'aapt2': run('aapt2-version', aapt, 'version').strip(),
                      'android_jar_sha256': hashlib.sha256((platform/'android.jar').read_bytes()).hexdigest(),
                      'provider_overlay_selected_in_binary': True,
                      'full_app_merged_manifest': 'NOT_VALIDATED_BY_THIS_PROBE',
                      'apk_build': 'NOT_RUN', 'android_runtime': 'NOT_TESTED'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
