"""Execute production color policies and mode transitions. No device FPS claims."""
import subprocess
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe
from test_glass_contrast import contrast, composite


def test_time_contrast_covers_transparency_gradients_and_extreme_backdrops(tmp_path):
    files = {'Probe.java': '''
import app.flexygram.bubbles.BubbleTimeContrast;
public class Probe {
 public static void main(String[] args) {
  BubbleTimeContrast c = new BubbleTimeContrast();
  for(int base:new int[]{0xffffff,0,0x808080,0xffee66,0x123456,0x27aaff})
   for(int alpha:new int[]{0,32,96,166,184,224,255})
    for(int ink:new int[]{0xff000000,0xffffffff,0xff757575,0xff4285f4,0x99555555}) {
     int surface=base|(alpha<<24);c.update(ink,surface);
     int result=c.ink(),backing=c.backing();
     for(int i=0;i<20000;i++) c.update(ink,surface);
     if(result!=c.ink()||backing!=c.backing())throw new AssertionError("unstable cache");
     System.out.println(Integer.toUnsignedString(surface)+" "+Integer.toUnsignedString(ink|0xff000000)+" "+Integer.toUnsignedString(result)+" "+Integer.toUnsignedString(backing));
    }
 }
}'''}
    actual = [JAVA/'app/exteraless/appearance/GlassContrastPolicy.java',
              JAVA/'app/flexygram/bubbles/BubbleTimeContrast.java']
    probe(tmp_path, files, actual)
    rows = subprocess.check_output(['java', '-cp', str(tmp_path), 'Probe'], text=True).splitlines()
    assert len(rows) == 210
    for row in rows:
        surface, original, ink, backing = map(int, row.split())
        for background in [0xff000000, 0xffffffff, 0xff777777, 0xffff0000, 0xff00ff00, 0xff0000ff]:
            visible = backing if backing else composite(surface, background)
            assert contrast(ink, visible) >= 4.5, row
        if surface >> 24 == 255 and contrast(original, surface) >= 4.5:
            assert ink == original and backing == 0


def test_independent_flags_and_retained_chat_sources_switch_without_reopening(tmp_path):
    shared = method((JAVA/'org/telegram/messenger/SharedConfig.java').read_text(), 'public static boolean chatBlurEnabled()')
    refresh = method((JAVA/'org/telegram/ui/ChatActivity.java').read_text(), 'private void refreshSignatureNativeGlassPolicy()')
    probe(tmp_path, {'Probe.java': '''
public class Probe {
 static class LiteMode {
  static final int FLAG_CHAT_BLUR=1,FLAG_LIQUID_GLASS=2;static int flags;
  static boolean isEnabled(int f){return (flags&f)!=0;}
 }
 static class SharedConfig {static boolean capable=true;static boolean canBlurChat(){return capable;}SHARED}
 static class DownscaleScrollableNoiseSuppressor {
  static final int DRAW_GLASS=0,DRAW_FROSTED_GLASS=1;static int builds;
  final boolean isLiquidGlassEnabled=LiteMode.isEnabled(LiteMode.FLAG_LIQUID_GLASS);
  DownscaleScrollableNoiseSuppressor(){builds++;}
 }
 static class Source {int updates;void setScrollableNoiseSuppressor(DownscaleScrollableNoiseSuppressor s,int index){updates++;}}
 static class Factory {boolean liquid;int changes;void setLiquidGlassEffectAllowed(boolean b){liquid=b;changes++;}}
 static class Bar {boolean liquid;void updateSignatureNativeGlassPolicy(boolean b){liquid=b;}}
 static class Input {boolean liquid;void updateNativeLiquidGlassPolicy(boolean b){liquid=b;}}
 static class View {void invalidate(){}}
 boolean signatureNativeGlassAllowed,signatureLiquidGlassAllowed;
 DownscaleScrollableNoiseSuppressor scrollableViewNoiseSuppressor=new DownscaleScrollableNoiseSuppressor();
 Source glassBackgroundSourceRenderNode=new Source(),glassBackgroundSourceFrostedRenderNode=new Source();
 Factory glassBackgroundDrawableFactory=new Factory(),glassBackgroundDrawableFactoryFrosted=new Factory();
 Bar actionBar=new Bar();Input chatInputViewsContainer=new Input();View contentView=new View();
 void invalidateMergedVisibleBlurredPositionsAndSourcesPositions(){}
 REFRESH
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){Probe p=new Probe();
  for(int flags:new int[]{2,1,3,0,1,2,0}) {
   LiteMode.flags=flags;p.refreshSignatureNativeGlassPolicy();
   check(SharedConfig.chatBlurEnabled()==(flags!=0));
   check(p.signatureNativeGlassAllowed==(flags!=0));
   boolean liquid=(flags&2)!=0;
   check(p.signatureLiquidGlassAllowed==liquid&&p.glassBackgroundDrawableFactory.liquid==liquid);
   check(p.glassBackgroundDrawableFactoryFrosted.liquid==liquid&&p.actionBar.liquid==liquid&&p.chatInputViewsContainer.liquid==liquid);
   check(p.scrollableViewNoiseSuppressor.isLiquidGlassEnabled==liquid);
   int builds=DownscaleScrollableNoiseSuppressor.builds,changes=p.glassBackgroundDrawableFactory.changes;
   for(int i=0;i<10000;i++)p.refreshSignatureNativeGlassPolicy();
   check(builds==DownscaleScrollableNoiseSuppressor.builds&&changes==p.glassBackgroundDrawableFactory.changes);
  }
  SharedConfig.capable=false;LiteMode.flags=3;check(!SharedConfig.chatBlurEnabled());
 }
}'''.replace('SHARED', shared).replace('REFRESH', refresh)})


def test_frosted_surface_keeps_transparency_and_theme_contrast(tmp_path):
    probe(tmp_path, {'Probe.java': '''
import app.exteraless.appearance.GlassContrastPolicy;
public class Probe {
 public static void main(String[] args){
  for(int color:new int[]{0x80ffffff,0xbbfafafc,0x44101018,0x88707070,0xcceeffcc}) {
   int s=GlassContrastPolicy.frostedSurface(color);
   if((s>>>24)<184||(s>>>24)==255)throw new AssertionError("lost frosted opacity");
   double black=GlassContrastPolicy.minimumContrast(0xff000000,s),white=GlassContrastPolicy.minimumContrast(0xffffffff,s);
   if(Math.max(black,white)<4.5)throw new AssertionError("unreadable surface");
  }
  if(GlassContrastPolicy.frostedSurface(0x00ffffff)!=0x00ffffff)throw new AssertionError("shadow-only tint");
  // Black and white alone are insufficient to test translucent mid-gray ink.
  if(GlassContrastPolicy.minimumContrast(0xff757575,0)!=1)throw new AssertionError("intermediate backdrop");
 }
}'''}, [JAVA/'app/exteraless/appearance/GlassContrastPolicy.java'])


def test_switch_updates_existing_drawables_and_releases_dead_owners(tmp_path):
    body = method((JAVA/'org/telegram/ui/Components/blur3/BlurredBackgroundDrawableViewFactory.java').read_text(), 'public void setLiquidGlassEffectAllowed(')
    probe(tmp_path, {'Probe.java': '''
import java.lang.ref.WeakReference;import java.util.ArrayList;
public class Probe {
 static class Build {static class VERSION{static int SDK_INT=33;}}
 static class BlurredBackgroundDrawable {int colors;void updateColors(){colors++;}}
 static class BlurredBackgroundDrawableRenderNode extends BlurredBackgroundDrawable {
  boolean refraction;void setLiquidGlassEffectAllowed(boolean b){refraction=b;}
 }
 boolean isLiquidGlassEffectAllowed;
 ArrayList<WeakReference<BlurredBackgroundDrawable>> createdDrawables=new ArrayList<>();
 BODY
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();
  BlurredBackgroundDrawableRenderNode header=new BlurredBackgroundDrawableRenderNode(),composer=new BlurredBackgroundDrawableRenderNode();
  p.createdDrawables.add(new WeakReference<>(header));p.createdDrawables.add(new WeakReference<>(composer));
  WeakReference<BlurredBackgroundDrawable> removed=new WeakReference<>(new BlurredBackgroundDrawable());removed.clear();p.createdDrawables.add(removed);
  p.setLiquidGlassEffectAllowed(true);check(header.refraction&&composer.refraction&&p.createdDrawables.size()==2);
  p.setLiquidGlassEffectAllowed(false);check(!header.refraction&&!composer.refraction&&header.colors==2&&composer.colors==2);
  Build.VERSION.SDK_INT=30;p.setLiquidGlassEffectAllowed(false);check(header.colors==3);
 }
}'''.replace('BODY', body)})


def test_alpha_animation_reuses_display_list_and_notifies_only_on_reentry(tmp_path):
    body = method((JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text(), 'public void setAlpha(int alpha)')
    probe(tmp_path, {'Probe.java': '''
public class Probe extends Base {
 static class Node {int updates;void setAlpha(float a){updates++;}}
 static class Source {int positions;void dispatchOnDrawablesRelativePositionChange(){positions++;}}
 Node renderNode=new Node();Source source=new Source();boolean renderNodeInvalidated;
 BODY
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){Probe p=new Probe();
  for(int i=0;i<10000;i++)p.setAlpha(255);check(p.renderNode.updates==0);
  for(int a=254;a>=0;a--)p.setAlpha(a);check(p.renderNode.updates==255&&!p.renderNodeInvalidated);
  p.setAlpha(255);check(p.source.positions==1);p.setAlpha(255);check(p.source.positions==1);
 }
}
class Base {int alpha=255;public int getAlpha(){return alpha;}public void setAlpha(int a){alpha=a;}}
'''.replace('BODY', body)})


def test_native_tint_tracks_mode_changes_without_overriding_explicit_alpha(tmp_path):
    probe(tmp_path, {
        'androidx/core/graphics/ColorUtils.java': 'package androidx.core.graphics;public class ColorUtils{}',
        'org/telegram/messenger/AndroidUtilities.java': 'package org.telegram.messenger;public class AndroidUtilities{public static float computePerceivedBrightness(int c){return .9f;}public static float dpf2(float f){return f;}}',
        'org/telegram/messenger/LiteMode.java': 'package org.telegram.messenger;public class LiteMode{public static final int FLAG_LIQUID_GLASS=2;public static boolean liquid;public static boolean isEnabled(int f){return liquid;}}',
        'org/telegram/ui/ActionBar/Theme.java': '''package org.telegram.ui.ActionBar;public class Theme{
 public interface ResourcesProvider{}public static final int key_windowBackgroundWhiteBlackText=1;
 public static int getColor(int id,ResourcesProvider r){return -1;}
 public static int multAlpha(int c,float a){return(c&0xffffff)|((int)(255*a)<<24);}}''',
        'org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundColorProvider.java': '''package org.telegram.ui.Components.blur3.drawable.color;public interface BlurredBackgroundColorProvider{
 int getShadowColor();int getBackgroundColor();int getStrokeColorTop();int getStrokeColorBottom();default int getStrokeColorFull(){return 0;}}''',
        'Probe.java': '''import org.telegram.messenger.LiteMode;import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProviderThemed;
public class Probe {public static void main(String[] a){
 BlurredBackgroundColorProviderThemed auto=new BlurredBackgroundColorProviderThemed(null,0),manual=new BlurredBackgroundColorProviderThemed(null,0,.4f);
 if((auto.getBackgroundColor()>>>24)!=193)throw new AssertionError();
 LiteMode.liquid=true;if((auto.getBackgroundColor()>>>24)!=216||(manual.getBackgroundColor()>>>24)!=102)throw new AssertionError();
 LiteMode.liquid=false;if((auto.getBackgroundColor()>>>24)!=193)throw new AssertionError();
 auto.setAlpha(.5f);LiteMode.liquid=true;if((auto.getBackgroundColor()>>>24)!=127)throw new AssertionError();
 }}'''
    }, [JAVA/'org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundColorProviderThemed.java'])
