"""Archive integrity, semantic coverage and actual default-loader JVM behavior."""
import hashlib
import json
import pathlib
import struct
import zlib
import subprocess

from test_render_work_reuse import JAVA, probe

# JAVA is .../TMessagesProj/src/main/java; resolve independently for shallow checkouts.
ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_packaged_pngs_are_unchanged_and_density_complete():
    manifest = json.loads((ROOT/'tools/exact_icons/assets.json').read_text())
    by_name = {}
    for asset in manifest:
        path = ROOT/asset['path']
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == asset['sha256']
        assert data[:8] == b'\x89PNG\r\n\x1a\n'
        assert '/drawable-night-' in asset['zip_path'], 'white pixels support legacy MULTIPLY tint'
        density = path.parent.name.split('-')[1]
        expected = {'mdpi':32, 'hdpi':48, 'xhdpi':64, 'xxhdpi':96, 'xxxhdpi':128}[density]
        assert struct.unpack('>II', data[16:24]) == (expected, expected)
        by_name.setdefault(path.stem, set()).add(density)
    assert len(by_name) == 119
    assert all(len(densities) == 5 for densities in by_name.values())
    assert sum((ROOT/a['path']).stat().st_size for a in manifest) < 1_400_000


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
    before = [(ROOT/p).read_bytes() for p in ['tools/exact_icons/mapping.json', 'TMessagesProj/src/main/java/app/flexygram/icons/ExactIconMap.java']]
    subprocess.run(['python', 'tools/exact_icons/generate.py'], cwd=ROOT, check=True, capture_output=True)
    assert before == [(ROOT/p).read_bytes() for p in ['tools/exact_icons/mapping.json', 'TMessagesProj/src/main/java/app/flexygram/icons/ExactIconMap.java']]
    data = json.loads((ROOT/'tools/exact_icons/mapping.json').read_text())
    for resource, expected in {
        'input_smile':'sticker', 'flexy_composer_folded':'sticker', 'input_attach':'adjuntar',
        'attach_send':'enviar', 'msg_callback':'llamar', 'fg_settings_chats':'mensaje_tres_puntos',
        'fg_settings_home':'apariencia', 'fg_settings_gesture':'controles', 'fg_settings_canales':'anuncios',
        'fg_settings_plugin':'plugin', 'fg_settings_folder':'carpeta', 'fg_settings_download':'descargar',
        'fg_settings_general':'panel', 'fg_settings_layers':'capas', 'fg_settings_comunidad':'idioma',
        'msg_unmute':'notificaciones', 'msg_mute':'notificaciones_silenciadas',
    }.items():
        assert data[resource]['asset'] == 'fg_ios_'+expected
    for resource in ['input_keyboard','player_new_repeatone','msg_unpin','msg_photo_crop','msg_photo_rotate','msg_photo_text2','msg_endcall']:
        assert resource not in data, 'preserve distinct actions absent from archive'
    assert not any(n.startswith('fg_ios_') for n in data), 'asset IDs must terminate recursion'
    names = {p.stem for p in (JAVA.parent/'res').glob('drawable*/*') if p.is_file()}
    assert set(data) <= names
    assert {v['asset'] for v in data.values()} <= names


def test_default_loader_retains_density_and_shares_pixels_without_sharing_view_state(tmp_path):
    data = json.loads((ROOT/'tools/exact_icons/mapping.json').read_text())
    names = sorted(set(data) | {v['asset'] for v in data.values()})
    # Non-final, deliberately non-lexical IDs exercise runtime map sorting.
    fields = ';'.join(f'public static int {name}={len(names)-i+100}' for i,name in enumerate(names))+';'
    files = {
        'org/telegram/messenger/R.java': 'package org.telegram.messenger;public class R {public static class drawable {'+fields+'}}',
        'app/exteraless/icons/BaseIconPacks.java': 'package app.exteraless.icons;public class BaseIconPacks {public static int BASE_DEFAULT=0, selected;public static int getSelected(){return selected;}}',
        'android/util/DisplayMetrics.java': 'package android.util;public class DisplayMetrics {public int densityDpi=320;}',
        'android/graphics/Bitmap.java': 'package android.graphics;public class Bitmap {}',
        'android/graphics/drawable/Drawable.java': '''package android.graphics.drawable;public abstract class Drawable {
            public int tint,alpha=255;public boolean mirrored;public abstract ConstantState getConstantState();
            public int getIntrinsicWidth(){return 0;}public int getIntrinsicHeight(){return 0;}
            public void setTint(int c){tint=c;}public void setAutoMirrored(boolean b){mirrored=b;}
            public abstract static class ConstantState {public abstract Drawable newDrawable();public Drawable newDrawable(android.content.res.Resources r){return newDrawable();}public abstract int getChangingConfigurations();}}''',
        'android/graphics/drawable/BitmapDrawable.java': '''package android.graphics.drawable;public class BitmapDrawable extends Drawable {
            android.graphics.Bitmap bitmap;public BitmapDrawable(android.content.res.Resources r,android.graphics.Bitmap b){bitmap=b;}
            public android.graphics.Bitmap getBitmap(){return bitmap;}public void setFilterBitmap(boolean b){}
            public ConstantState getConstantState(){return null;}}''',
        'android/content/res/Resources.java': '''package android.content.res;public class Resources {
            public static class Theme {}public int depth,maxDepth,decodes;public java.util.Map<Long,android.graphics.Bitmap> pixels=new java.util.HashMap<>();
            android.util.DisplayMetrics metrics=new android.util.DisplayMetrics();public android.util.DisplayMetrics getDisplayMetrics(){return metrics;}
            public android.graphics.drawable.Drawable getDrawableForDensity(int id,int density,Theme theme){
                depth++;maxDepth=Math.max(depth,maxDepth);
                android.graphics.drawable.Drawable exact=app.flexygram.icons.ExactIcons.create(this,id,density,theme);
                if(exact!=null){depth--;return exact;}
                long key=((long)id<<32)|density;android.graphics.Bitmap bitmap=pixels.get(key);
                if(bitmap==null){bitmap=new android.graphics.Bitmap();pixels.put(key,bitmap);decodes++;}
                depth--;return new android.graphics.drawable.BitmapDrawable(this,bitmap);
            }}''',
        'Probe.java': '''import android.content.res.Resources;import android.graphics.drawable.*;import app.flexygram.icons.ExactIcons;import app.exteraless.icons.BaseIconPacks;import org.telegram.messenger.R;
        public class Probe {
            static void check(boolean b){if(!b)throw new AssertionError();}
            public static void main(String[] args){
                Resources r=new Resources();
                BitmapDrawable a=(BitmapDrawable)r.getDrawableForDensity(R.drawable.input_smile,0,null);
                BitmapDrawable b=(BitmapDrawable)r.getDrawableForDensity(R.drawable.input_smile,0,null);
                check(a!=b&&a.getBitmap()==b.getBitmap()&&r.decodes==1&&r.maxDepth==2);
                a.setTint(123);a.alpha=34;check(b.tint!=123&&b.alpha==255);
                check(a.getIntrinsicWidth()==56&&a.getIntrinsicHeight()==56);
                Drawable c=ExactIcons.create(r,R.drawable.input_smile,480,null);check(c.getIntrinsicWidth()==84);
                r.getDisplayMetrics().densityDpi=160;Drawable copy=a.getConstantState().newDrawable(r);
                check(copy!=a&&copy.getIntrinsicWidth()==28&&((BitmapDrawable)copy).getBitmap()==a.getBitmap());
                check(ExactIcons.create(r,0,0,null)==null&&ExactIcons.create(r,-1,0,null)==null);
                check(ExactIcons.create(r,R.drawable.fg_ios_sticker,0,null)==null);
                for(int type=1;type<=3;type++){BaseIconPacks.selected=type;check(ExactIcons.create(r,R.drawable.input_smile,0,null)==null);}
            }
        }''',
    }
    for name in ['ExactIcons.java','ExactIconMap.java']:
        files['app/flexygram/icons/'+name] = (JAVA/'app/flexygram/icons'/name).read_text()
    probe(tmp_path, files, [])
