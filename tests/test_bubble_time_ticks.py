"""Normal timestamp paint and native iOS-style check defaults; no device claim."""
import re
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


def test_ios_tick_native_factory_dimensions_and_build_fallback(tmp_path):
    source=(JAVA/'org/telegram/ui/ActionBar/Theme.java').read_text()
    start=source.index('            // Native FlexyGram defaults:')
    block=source[start:source.index('            chat_msgClockDrawable',start)]
    fields=re.findall(r'^\s+(chat_msg\w+) = resources',block,re.M)
    assert len(fields)==10
    declarations='\n'.join('Drawable '+f+';' for f in fields)
    probe(tmp_path, {'Probe.java': '''public class Probe {
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
}'''.replace('FIELDS',declarations).replace('BLOCK',block.replace('app.flexygram.bubbles.BubbleStyle.signature()','signature')).replace('CHECKS','\n'.join(
        f'if(p.{f}.resource != (enabled ? {2 if "Half" in f else 1} : {5 if "Half" in f and ("Media" in f or "Sticker" in f) else 4 if "Half" in f else 3}))throw new AssertionError("{f}");'
        for f in fields))})
    ns='{http://schemas.android.com/apk/res/android}'
    for name in ['flexy_check_ios27','flexy_halfcheck_ios27']:
        vector=ET.parse(ROOT/f'TMessagesProj/src/main/res/drawable/{name}.xml').getroot()
        assert vector.get(ns+'width')==vector.get(ns+'height')=='12dp'
        assert vector.get(ns+'viewportWidth')==vector.get(ns+'viewportHeight')=='12'
        path=vector.find('path')
        assert path.get(ns+'strokeLineCap')==path.get(ns+'strokeLineJoin')=='round'
        assert path.get(ns+'strokeWidth')=='1.25'
    preview=(JAVA/'app/flexygram/bubbles/BubblePreviewView.java').read_text()
    assert 'R.drawable.flexy_check_ios27' in preview and 'R.drawable.flexy_halfcheck_ios27' in preview
