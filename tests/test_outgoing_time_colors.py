"""Outgoing gradient metadata stays secondary; explicit theme colors and paint are retained."""
import subprocess
from test_render_work_reuse import JAVA, probe
from test_glass_contrast import contrast


def test_secondary_gradient_ink_has_tint_and_preserves_readable_polarity(tmp_path):
    probe(tmp_path, {'Probe.java': '''
import app.flexygram.bubbles.BubbleTimeColors;
public class Probe {
 public static void main(String[] args) {
  for(int surface:new int[]{0xff184c2b,0xff50934d,0xff17212b,0xff2481cc,0xff000000,
                            0xffffffff,0xfff3e0a0,0xffdfefde,0xff777777})
   for(int primary:new int[]{0xffffffff,0xff000000}) {
    int result=BubbleTimeColors.gradientSecondary(primary,surface);
    System.out.println(Integer.toUnsignedString(primary)+" "+Integer.toUnsignedString(surface)+" "+Integer.toUnsignedString(result));
   }
 }
}'''}, [JAVA/'app/exteraless/appearance/GlassContrastPolicy.java',
        JAVA/'app/flexygram/bubbles/BubbleTimeColors.java'])
    rows=subprocess.check_output(['java','-cp',str(tmp_path),'Probe'],text=True).splitlines()
    for row in rows:
        primary,surface,result=map(int,row.split())
        assert result >> 24 == 255  # no alpha applied to shared time paint
        assert contrast(result,surface) >= min(3,contrast(primary,surface))-0.02
        assert contrast(result,surface) <= contrast(primary,surface)+0.02
        for shift in (0,8,16):
            a,b,c=((color>>shift)&255 for color in (primary,surface,result))
            assert min(a,b) <= c <= max(a,b)
        if contrast(primary,surface)>4 and primary!=surface:
            assert result!=primary  # actual secondary ink, not message white/black


def test_theme_uses_secondary_ink_without_overwriting_custom_time_colors(tmp_path):
    source=(JAVA/'org/telegram/ui/ActionBar/Theme.java').read_text()
    start=source.index('                        int timeColor = app.flexygram.bubbles.BubbleTimeColors.')
    block=source[start:source.index('                        currentColors.put(key_chat_outAudioDurationText',start)]
    probe(tmp_path, {'Probe.java': '''
import java.util.HashMap;
public class Probe {
 static final int key_chat_outTimeText=1,key_chat_outTimeSelectedText=2;
 static class Colors extends HashMap<Integer,Integer> {
  int get(int key){return getOrDefault(key,0);}int get(int key,int fallback){return getOrDefault(key,fallback);}
  int indexOfKey(int key){return containsKey(key)?0:-1;}
 }
 Colors currentColorsNoAccent=new Colors(),currentColors=new Colors();
 void apply(int textColor,int timeSurface) {BLOCK}
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args) {
  Probe p=new Probe();p.apply(0xffffffff,0xff184c2b);
  int secondary=p.currentColors.get(1);
  check(secondary!=0xffffffff&&secondary==p.currentColors.get(2));
  p.currentColorsNoAccent.put(1,0xff82b879);p.currentColors.put(1,0xff82b879);
  p.currentColorsNoAccent.put(2,0xff93c98a);p.currentColors.put(2,0xff93c98a);
  p.apply(0xffffffff,0xff184c2b);
  check(p.currentColors.get(1)==0xff82b879&&p.currentColors.get(2)==0xff93c98a);
  p.currentColorsNoAccent.put(1,0xffffffff);p.currentColors.put(1,0xffffffff);
  p.apply(0xffffffff,0xff184c2b);check(p.currentColors.get(1)==secondary);
  p.currentColors.clear();p.currentColorsNoAccent.clear();p.apply(0xff000000,0xffdfefde);
  check(p.currentColors.get(1)!=0xff000000&&p.currentColors.get(1)!=secondary);
 }
}'''.replace('BLOCK',block)}, [JAVA/'app/exteraless/appearance/GlassContrastPolicy.java',
                                            JAVA/'app/flexygram/bubbles/BubbleTimeColors.java'])
