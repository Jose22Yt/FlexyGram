"""Build small splash vectors from the existing icon artwork; no raster copies or new assets."""
from pathlib import Path
import copy
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'TMessagesProj/src/main/res'
ANDROID = 'http://schemas.android.com/apk/res/android'
AAPT = 'http://schemas.android.com/aapt'
A = '{' + ANDROID + '}'
ET.register_namespace('android', ANDROID)
ET.register_namespace('aapt', AAPT)


def generate():
    controller = (ROOT / 'TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java').read_text()
    aliases = {a.get(A + 'name').split('.')[-1]: a for a in
               ET.parse(ROOT / 'TMessagesProj/src/main/AndroidManifest.xml').findall('./application/activity-alias')}
    entries = re.findall(r'^        (\w+)\("(\w+)", R\.(?:drawable|mipmap)\.(\w+),\s*R\.(?:drawable|mipmap)\.(\w+)', controller, re.M)
    styles = ET.Element('resources')
    base = ET.SubElement(styles, 'style', {'name': 'Theme.FlexyGram.Start', 'parent': 'Theme.TMessages.Start'})
    for name, value in {
        'android:windowBackground': '@color/SplashBackground',
        'android:windowSplashScreenBackground': '@color/SplashBackground',
        'android:windowSplashScreenAnimatedIcon': '@drawable/flexy_startup_flex_neon',
        'android:windowSplashScreenIconBackgroundColor': '@android:color/transparent',
        'android:windowSplashScreenAnimationDuration': '0',
    }.items():
        ET.SubElement(base, 'item', {'name': name}).text = value
    for name, key, bg, fg in entries:
        if name.startswith('FLEX_') or name == 'EXTERALESS':
            background = ET.parse(RES / 'drawable' / (bg + '.xml')).getroot()
            foreground = ET.parse(RES / 'drawable' / (fg + '.xml')).getroot()
            vector = ET.Element('vector', {A+'width': '288dp', A+'height': '288dp', A+'viewportWidth': '162', A+'viewportHeight': '162'})
            group = ET.SubElement(vector, 'group', {A+'translateX': '27', A+'translateY': '27'})
            # 192dp circle inside the platform's 288dp icon area; no device-dependent adaptive mask.
            ET.SubElement(group, 'clip-path', {A+'pathData': 'M54,0 A54,54 0,1 1,54,108 A54,54 0,1 1,54,0 Z'})
            path = ET.SubElement(group, 'path', {A+'pathData': 'M0,0 H108 V108 H0 Z'})
            solid = background.find('solid')
            if solid is not None:
                path.set(A+'fillColor', solid.get(A+'color'))
            else:
                gradient = background.find('gradient')
                assert gradient is not None and gradient.get(A+'angle') == '315', bg
                fill = ET.SubElement(path, '{'+AAPT+'}attr', {'name': 'android:fillColor'})
                grad = ET.SubElement(fill, 'gradient', {A+'startX': '-27', A+'startY': '-27', A+'endX': '135', A+'endY': '135', A+'type': 'linear'})
                for offset, key_color in [('0', 'startColor'), ('0.5', 'centerColor'), ('1', 'endColor')]:
                    ET.SubElement(grad, 'item', {A+'offset': offset, A+'color': gradient.get(A+key_color)})
            # Same 108dp adaptive layers / 72dp visible area as the existing icon picker.
            art = ET.SubElement(group, 'group', {A+'scaleX': '1.5', A+'scaleY': '1.5', A+'pivotX': '54', A+'pivotY': '54'})
            for child in foreground:
                art.append(copy.deepcopy(child))
            ET.indent(vector)
            (RES / 'drawable-v24').mkdir(exist_ok=True)
            (RES / 'drawable-v24' / ('flexy_startup_' + name.lower() + '.xml')).write_text(ET.tostring(vector, encoding='unicode') + '\n')
            icon = '@drawable/flexy_startup_' + name.lower()
        else:
            # Legacy icons keep their existing adaptive/round resources, with no duplicate bitmaps.
            icon = aliases[key].get(A+'roundIcon')
        style = ET.SubElement(styles, 'style', {'name': 'Theme.FlexyGram.Start.'+name, 'parent': 'Theme.FlexyGram.Start'})
        ET.SubElement(style, 'item', {'name': 'android:windowSplashScreenAnimatedIcon'}).text = icon
    ET.indent(styles)
    (RES / 'values-v31/flexygram_startup.xml').write_text(ET.tostring(styles, encoding='unicode') + '\n')
    # Android 13 can otherwise choose a solid-color splash for some launch paths.
    modern = ET.Element('resources')
    modern_base = copy.deepcopy(base)
    ET.SubElement(modern_base, 'item', {'name': 'android:windowSplashScreenBehavior'}).text = 'icon_preferred'
    modern.append(modern_base)
    ET.indent(modern)
    (RES / 'values-v33').mkdir(exist_ok=True)
    (RES / 'values-v33/flexygram_startup.xml').write_text(ET.tostring(modern, encoding='unicode') + '\n')
    # Before Android 12 the starting window is static. Reuse its native background; no extra activity.
    legacy = '''<resources xmlns:android="http://schemas.android.com/apk/res/android">
    <style name="Theme.FlexyGram.Start" parent="Theme.TMessages.Start">
        <item name="android:windowBackground">@color/SplashBackground</item>
    </style>
</resources>
'''
    (RES / 'values/flexygram_startup.xml').write_text(legacy)
    return [name for name, *_ in entries]


if __name__ == '__main__':
    print('Generated native splash resources for', len(generate()), 'icons')
