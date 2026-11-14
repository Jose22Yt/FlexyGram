"""Generate icon-free starting themes, preserving names persisted by Android on older installs."""
from pathlib import Path
import copy
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'TMessagesProj/src/main/res'


def generate():
    controller = (ROOT / 'TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java').read_text()
    names = re.findall(r'^        (\w+)\("\w+", R\.(?:drawable|mipmap)\.', controller, re.M)
    styles = ET.Element('resources')
    base = ET.SubElement(styles, 'style', {'name': 'Theme.FlexyGram.Start', 'parent': 'Theme.TMessages.Start'})
    for name, value in {
        'android:windowBackground': '@color/SplashBackground',
        'android:windowDisablePreview': 'true',
        'android:windowSplashScreenBackground': '@color/SplashBackground',
        'android:windowSplashScreenAnimatedIcon': '@drawable/flexy_startup_empty',
        'android:windowSplashScreenIconBackgroundColor': '@android:color/transparent',
        'android:windowSplashScreenAnimationDuration': '0',
    }.items():
        ET.SubElement(base, 'item', {'name': name}).text = value
    # Android may still remember an old per-icon theme after an app update.
    # Keep those resource names working, with the same empty starting content.
    for name in names:
        ET.SubElement(styles, 'style', {'name': 'Theme.FlexyGram.Start.' + name, 'parent': 'Theme.FlexyGram.Start'})
    ET.indent(styles)
    (RES / 'values-v31/flexygram_startup.xml').write_text(ET.tostring(styles, encoding='unicode') + '\n')
    modern = ET.Element('resources')
    modern_base = copy.deepcopy(base)
    ET.SubElement(modern_base, 'item', {'name': 'android:windowSplashScreenBehavior'}).text = 'default'
    modern.append(modern_base)
    ET.indent(modern)
    (RES / 'values-v33/flexygram_startup.xml').write_text(ET.tostring(modern, encoding='unicode') + '\n')
    legacy = ET.Element('resources')
    legacy_base = ET.SubElement(legacy, 'style', {'name': 'Theme.FlexyGram.Start', 'parent': 'Theme.TMessages.Start'})
    ET.SubElement(legacy_base, 'item', {'name': 'android:windowBackground'}).text = '@color/SplashBackground'
    ET.SubElement(legacy_base, 'item', {'name': 'android:windowDisablePreview'}).text = 'true'
    ET.indent(legacy)
    (RES / 'values/flexygram_startup.xml').write_text(ET.tostring(legacy, encoding='unicode') + '\n')
    return names


if __name__ == '__main__':
    print('Generated icon-free startup themes with', len(generate()), 'compatible legacy names')
