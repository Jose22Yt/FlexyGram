"""Original upstream provenance, exact point sizes, semantic states and loader behavior."""
import math
import hashlib
import json
import pathlib
import struct
import zlib
import subprocess
import xml.etree.ElementTree as ET
from test_render_work_reuse import JAVA, probe
ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_original_provenance_and_native_resource_dimensions():
    manifest=json.loads((ROOT/'tools/ios_originals/manifest.json').read_text())
    assert manifest['repository']=='TelegramMessenger/Telegram-iOS'
    assert manifest['commit']=='24638bc69bd083981b178dd1e7f921eebbf7fc46'
    assets=manifest['assets'];assert len(assets)>=190
    a='{http://schemas.android.com/apk/res/android}'
    total=0
    for asset in assets:
        assert asset['template'] and asset['width_dp']>0 and asset['height_dp']>0
        for item in asset['sources']+asset['outputs']:
            data=(ROOT/item['path']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==item['sha256'],item['path']
            if 'git_blob'in item:
                assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==item['git_blob']
        for output in asset['outputs']:
            path=ROOT/output['path'];data=path.read_bytes();total+=len(data)
            if path.suffix=='.xml':
                vector=ET.fromstring(data)
                assert math.isclose(float(vector.get(a+'width').removesuffix('dp')),asset['width_dp'],abs_tol=1e-7)
                assert math.isclose(float(vector.get(a+'height').removesuffix('dp')),asset['height_dp'],abs_tol=1e-7)
                assert math.isclose(float(vector.get(a+'viewportWidth')),asset['width_dp'],abs_tol=1e-7)
                assert math.isclose(float(vector.get(a+'viewportHeight')),asset['height_dp'],abs_tol=1e-7)
            else:
                density=path.parent.name.split('-')[1];scale={'mdpi':1,'hdpi':1.5,'xhdpi':2,'xxhdpi':3,'xxxhdpi':4}[density]
                w,h=struct.unpack('>II',data[16:24])
                assert abs(w-asset['width_dp']*scale)<=1 and abs(h-asset['height_dp']*scale)<=1
        if asset['kind']=='original-lottie-final-frame':
            source=next(s for s in asset['sources'] if s['path'].endswith('.json'))
            obj=json.loads((ROOT/source['path']).read_text())
            assert asset['frame']==int(obj['op']-obj.get('ip',0))-1
    assert total<1_000_000
    assert not list((JAVA.parent/'res').glob('drawable*/fg_ios_sticker.png'))


def test_visible_source_pixels_accept_legacy_multiply_tints():
    # Decode the smallest original PNG of each symbol without an image dependency.
    # Multiplying a black source by a theme colour would leave the glyph black.
    for path in (JAVA.parent/'res/drawable-mdpi').glob('fg_ios_*.png'):
        png = path.read_bytes()
        width, height, depth, colour = struct.unpack('>IIBB', png[16:26])
        assert (depth, colour) == (8, 6), path
        packed = bytearray()
        pos = 8
        while pos < len(png):
            length = struct.unpack('>I', png[pos:pos+4])[0]
            if png[pos+4:pos+8] == b'IDAT':
                packed.extend(png[pos+8:pos+8+length])
            pos += length+12
        raw = zlib.decompress(packed)
        stride = width*4
        previous = bytearray(stride)
        visible = 0
        for y in range(height):
            offset = y*(stride+1)
            kind = raw[offset]
            row = bytearray(raw[offset+1:offset+stride+1])
            assert 0 <= kind <= 4
            for x in range(stride):
                left = row[x-4] if x >= 4 else 0
                above = previous[x]
                corner = previous[x-4] if x >= 4 else 0
                if kind == 1: predictor = left
                elif kind == 2: predictor = above
                elif kind == 3: predictor = (left+above)//2
                elif kind == 4:
                    p = left+above-corner
                    a, b, c = abs(p-left), abs(p-above), abs(p-corner)
                    predictor = left if a <= b and a <= c else above if b <= c else corner
                else: predictor = 0
                row[x] = (row[x]+predictor)&255
            for x in range(0, stride, 4):
                if row[x+3]:
                    visible += 1
                    assert row[x:x+3] == b'\xff\xff\xff', path
            previous = row
        assert visible, path


def test_semantics_and_regeneration():
    subprocess.run(['python','tools/ios_originals/generate.py','--check'],cwd=ROOT,check=True,capture_output=True)
    paths=['tools/exact_icons/mapping.json','TMessagesProj/src/main/java/app/flexygram/icons/ExactIconMap.java']
    before=[(ROOT/p).read_bytes()for p in paths]
    subprocess.run(['python','tools/exact_icons/generate.py'],cwd=ROOT,check=True,capture_output=True)
    assert before==[(ROOT/p).read_bytes()for p in paths]
    data=json.loads((ROOT/paths[0]).read_text());assert len(data)>=1000
    for resource,key in {
        'input_smile':'@animation:input_anim_keyToSticker.json',
        'flexy_composer_folded':'@animation:input_anim_keyToSticker.json',
        'input_keyboard':'@animation:input_anim_stickerToKey.json',
        'input_attach':'Chat/Input/Text/IconAttachment',
        'attach_send':'Chat/Input/Text/SendIcon',
        'msg_unpin':'Chat/Context Menu/Unpin',
        'player_new_repeatone':'GlobalMusicPlayer/RepeatOne',
        'msg_photo_rotate':'Media Editor/Rotate',
        'msg_endcall':'Call/CallDeclineButton',
        'fg_settings_chats':'Chat/Context Menu/MessageBubble',
        'fg_settings_home':'Chat/Context Menu/Palette',
        'fg_settings_gesture':'Item List/Icons/Hand',
        'fg_settings_plugin':'Chat/Context Menu/Apps',
        'fg_settings_download':'Chat/Context Menu/Download',
    }.items():assert data[resource]['key']==key
    for x,y in [('msg_mute','msg_unmute'),('msg_pin','msg_unpin'),('msg_markread','msg_markunread'),('input_mic','input_video')]:
        assert data[x]['asset']!=data[y]['asset']
    names={p.stem for p in (JAVA.parent/'res').glob('drawable*/*')if p.is_file()}
    assert set(data)<=names and {v['asset']for v in data.values()}<=names
    assert not any(n.startswith('fg_ios_')for n in data)


def test_native_loader_size_tint_state_and_density_isolation(tmp_path):
    from ios_icons_stubs import fixtures
    files=fixtures()
    files['Probe.java']=r"""import android.content.res.Resources;import android.graphics.*;import android.graphics.drawable.*;
import app.flexygram.icons.ExactIcons;import app.exteraless.icons.BaseIconPacks;import org.telegram.messenger.R;
public class Probe {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  Resources r=new Resources();Canvas c=new Canvas();
  Drawable a=r.getDrawableForDensity(R.drawable.input_smile,0,null),b=r.getDrawableForDensity(R.drawable.input_smile,0,null);
  check(a!=b&&r.decodes==1&&r.maxDepth==2&&a.getIntrinsicWidth()==64&&a.getIntrinsicHeight()==64);
  a.setTint(123);a.setAlpha(34);a.setState(new int[]{7});a.setLevel(19);a.setColorFilter(new ColorFilter());a.setAutoMirrored(true);a.setLayoutDirection(1);
  a.setBounds(0,0,100,80);a.draw(c);Fake first=c.last;check(first.tint==123&&first.alpha==34&&first.getLevel()==19&&first.getState()[0]==7&&first.mirrored&&first.getLayoutDirection()==1);
  check(first.getBounds().left==18&&first.getBounds().top==8&&first.getBounds().width()==64&&first.getBounds().height()==64);
  b.draw(c);check(c.last!=first&&c.last.pixels==first.pixels&&c.last.tint!=123&&c.last.alpha==255&&c.last.filter==null);
  Drawable copy=a.getConstantState().newDrawable(r);copy.setTint(222);copy.draw(c);check(c.last.tint==222);a.draw(c);check(c.last.tint==123);
  Drawable dense=ExactIcons.create(r,R.drawable.input_smile,480,null);check(dense.getIntrinsicWidth()==96);
  Resources low=new Resources();low.density=160;Drawable lowCopy=a.getConstantState().newDrawable(low);check(lowCopy.getIntrinsicWidth()==32);
  Drawable rectangle=ExactIcons.create(r,R.drawable.input_attach,0,null);check(rectangle.getIntrinsicWidth()==60&&rectangle.getIntrinsicHeight()==40);
  rectangle.setBounds(0,0,30,30);rectangle.draw(c);check(c.last.getBounds().width()==30&&c.last.getBounds().height()==20&&c.last.getBounds().top==5);
  rectangle.setBounds(0,0,120,120);rectangle.draw(c);check(c.last.getBounds().width()==60&&c.last.getBounds().height()==40);
  check(ExactIcons.create(r,0,0,null)==null&&ExactIcons.create(r,-1,0,null)==null&&ExactIcons.create(r,R.drawable.fg_ios_original_animation_input_anim_keytosticker_json,0,null)==null);
  BaseIconPacks.selected=3;check(ExactIcons.create(r,R.drawable.input_smile,0,null)!=null);
  for(int type=1;type<=2;type++){BaseIconPacks.selected=type;check(ExactIcons.create(r,R.drawable.input_smile,0,null)==null&&ExactIcons.direct(R.drawable.input_smile)==null);}
 }
}"""
    actual=[JAVA/'app/flexygram/icons'/n for n in ['ExactIcons.java','ExactIconMap.java','OriginalIconDrawable.java']]
    probe(tmp_path,files,actual)
