"""Normal timestamp paint and native iOS-style check defaults; no device claim."""
import re
import subprocess
import pytest
import xml.etree.ElementTree as ET
from test_composer_layout import method
from test_render_work_reuse import JAVA, ROOT, probe


def test_time_is_one_theme_draw_without_paint_mutation(tmp_path):
    source=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    draw=method(source,'private void drawReadableTimeLayout(')
    probe(tmp_path, {'Probe.java': '''public class Probe {
 static class Canvas{}
 static class TextPaint{int ink;TextPaint(int c){ink=c;}int getColor(){return ink;}void setColor(int c){ink=c;}}
 static class Theme{static TextPaint chat_timePaint=new TextPaint(0x7fffffff);}
 static class StaticLayout{TextPaint paint;int draws,drawn;StaticLayout(int ink){paint=new TextPaint(ink);}TextPaint getPaint(){return paint;}}
 static class SpoilerEffect {static void layoutDrawMaybe(StaticLayout l,Canvas c){l.draws++;l.drawn=l.paint.ink;}}
 DRAW
 public static void main(String[] args){Probe p=new Probe();Canvas canvas=new Canvas();
 for(int color:new int[]{0xff888888,0xffffffff,0xff000000,0x55444444})for(boolean selected:new boolean[]{false,true}){
 StaticLayout layout=new StaticLayout(color);for(int i=0;i<1000;i++)p.drawReadableTimeLayout(canvas,layout,selected);
 if(layout.paint.ink!=color||layout.draws!=1000||layout.drawn!=Theme.chat_timePaint.ink)throw new AssertionError();
 }
 p.drawReadableTimeLayout(canvas,null,false);
 }
}'''.replace('DRAW',draw)})


@pytest.mark.parametrize("native", [False, True])
def test_ios_tick_native_factory_dimensions_and_build_fallback(tmp_path, native):
    source=(JAVA/'org/telegram/ui/ActionBar/Theme.java').read_text()
    start=source.index('            // Native FlexyGram defaults:')
    block=source[start:source.index('            chat_msgClockDrawable',start)]
    fields=re.findall(r'^\s+(chat_msg\w+) = resources',block,re.M)
    assert len(fields)==10
    declarations='\n'.join('Drawable '+f+';' for f in fields)
    probe(tmp_path, {'org/telegram/messenger/BuildConfig.java':'package org.telegram.messenger;public class BuildConfig{public static final boolean CONNECTED_ALPHA=true,NATIVE_BASELINE_TEST='+str(native).lower()+';}', 'Probe.java': '''public class Probe {
 static boolean signature;
 static class Drawable {int resource;Drawable(int r){resource=r;}Drawable mutate(){return this;}}
 static class Resources{Drawable getDrawable(int r){return new Drawable(r);}}
 static class R{static class drawable{static int flexy_check_ios27=1,flexy_halfcheck_ios27=2,msg_check_s=3,msg_halfcheck=4,msg_halfcheck_s=5;}}
 Resources resources=new Resources();FIELDS
 void init(){BLOCK}
 public static void main(String[] args){Probe p=new Probe();for(boolean enabled:new boolean[]{true,false}){
 signature=enabled;p.init();
 CHECKS
 }}
}'''.replace('FIELDS',declarations).replace('BLOCK',block.replace('BuildConfig.CONNECTED_ALPHA','signature')).replace('CHECKS','\n'.join(
        f'if(p.{f}.resource != (enabled ? {2 if "Half" in f else 1} : {5 if "Half" in f and ("Media" in f or "Sticker" in f) else 4 if "Half" in f else 3}))throw new AssertionError("{f}");'
        for f in fields))})
    ns='{http://schemas.android.com/apk/res/android}'
    for name in ['flexy_check_ios27','flexy_halfcheck_ios27']:
        vector=ET.parse(ROOT/f'TMessagesProj/src/main/res/drawable/{name}.xml').getroot()
        assert vector.get(ns+'width')=='11dp' and vector.get(ns+'height')=='9dp'
        assert vector.get(ns+'viewportWidth')=='11' and vector.get(ns+'viewportHeight')=='9'
        path=vector.find('path')
        assert path.get(ns+'strokeLineCap')==path.get(ns+'strokeLineJoin')=='round'
        assert path.get(ns+'strokeWidth')=='0.99'
    preview=(JAVA/'app/flexygram/bubbles/BubblePreviewView.java').read_text()
    assert 'R.drawable.flexy_check_ios27' in preview and 'R.drawable.flexy_halfcheck_ios27' in preview


def test_ios_status_placement_and_resource_set_match_the_flexygram_backup():
    backup='9b305e3ee7ee16097576d60af07f6ed9f105de9c'
    def original(path):
        return subprocess.check_output(['git','show',backup+':TMessagesProj/src/main/java/'+path],cwd=ROOT,text=True)
    path='org/telegram/ui/Cells/ChatMessageCell.java'
    assert method((JAVA/path).read_text(),'private void drawStatusDrawable(')==method(original(path),'private void drawStatusDrawable(')
    path='org/telegram/ui/ActionBar/Theme.java'
    def factory(source):
        start=source.index('            // Native FlexyGram defaults:')
        return source[start:source.index('            chat_msgClockDrawable',start)]
    assert factory((JAVA/path).read_text())==factory(original(path))
    for field in ['dialogs_checkDrawable','dialogs_checkReadDrawable','dialogs_halfCheckDrawable']:
        current=next(line.strip() for line in (JAVA/path).read_text().splitlines() if line.strip().startswith(field+' ='))
        previous=next(line.strip() for line in original(path).splitlines() if line.strip().startswith(field+' ='))
        assert current==previous
