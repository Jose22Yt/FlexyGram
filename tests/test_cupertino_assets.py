"""Asset/mapping integrity: broken shipped glyphs must not silently replace native icons."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'tools/cupertino'
JAVA=ROOT/'TMessagesProj/src/main/java'

def test_cupertino_catalog_matches_shipped_assets_and_generated_resource_map():
    mapping=json.loads((TOOLS/'mapping.json').read_text())
    catalog=json.loads((TOOLS/'catalog.json').read_text())
    upstream=json.loads((TOOLS/'UPSTREAM.json').read_text())
    asset=TOOLS/'reference/assets/cupertino/CupertinoIcons.ttf'
    assert hashlib.sha256(asset.read_bytes()).hexdigest()==upstream['font_sha256']
    source=(TOOLS/'reference/src/app/flexygram/icons/CupertinoIconMap.java').read_text()
    specs=source[source.index('private static long[] buildSpecs()'):source.index('private static long[] buildColors()')]
    ids=set(re.findall(r'R.drawable.(\w+) << 32',specs))
    assert ids==mapping.keys()
    resources={p.stem for p in (ROOT/'TMessagesProj/src/main/res').glob('drawable*/*')}
    for name,spec in mapping.items():
        assert name in resources
        assert catalog[spec['glyph']]==spec['codepoint']
        assert 4<=spec['width']<=96 and 4<=spec['height']<=96
        packed=spec['codepoint']|(spec['width']<<16)|(spec['height']<<24)|(0x80000000 if spec['mirrored'] else 0)
        assert f'((long) R.drawable.{name} << 32) | 0x{packed:08x}L' in specs
    assert {'msg_settings','input_attach','input_mic','flexy_composer_send','fg_settings_chat','menu_reply'}<=ids
    assert {'msg_halfcheck','msg_autodelete_1d','profile_level10_inner'}.isdisjoint(ids)

def test_cupertino_notices_ship_without_a_flutter_runtime():
    assets=ROOT/'TMessagesProj/src/main/assets'
    assert (assets/'licenses/cupertino-icons-MIT.txt').read_bytes()==(TOOLS/'reference/assets/cupertino/LICENSE').read_bytes()
    assert (assets/'licenses/flutter-cupertino-catalog-BSD.txt').read_bytes()==(TOOLS/'FLUTTER-LICENSE').read_bytes()
    assert not (assets/'cupertino/CupertinoIcons.ttf').exists()
    assert {p.name for p in (JAVA/'app/flexygram/icons').glob('*.java')} == {'SignatureLauncherUpdateReceiver.java'}


def test_native_icon_resources_are_restored_without_overriding_user_packs():
    # There must be no active Cupertino resource wrapper, menu substitution or touch observer.
    for path in JAVA.rglob('*.java'):
        if path.is_relative_to(JAVA/'app/flexygram/icons'):
            continue
        source=path.read_text()
        assert 'CupertinoIcons.create(' not in source, str(path)
        assert 'new app.flexygram.icons.CupertinoResources(' not in source, str(path)
        assert 'IconPressFeedback.observe(' not in source, str(path)
    packs=(JAVA/'app/exteraless/icons/BaseIconPacks.java').read_text()
    assert 'return "Cupertino Icons";' not in packs
    assert 'return org.telegram.messenger.LocaleController.getString(R.string.Default);' in packs
    loader=(JAVA/'tw/nekomimi/nekogram/ui/icons/IconsResources.java').read_text()
    assert 'IconPackManager.getInstance().getDrawable(this, id, density, theme)' in loader
    assert 'getConversion(id)' in loader
