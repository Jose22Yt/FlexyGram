"""Execute the actual composer draw pass: menu snapshots cannot hide retained HWUI surfaces."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_software_menu_captures_preserve_live_backgrounds_and_restore_owner_on_failure(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    draw=method(source[source.index('    /* Render */'):],'protected void dispatchDraw(@NonNull Canvas canvas)').replace('@NonNull ','')
    probe(tmp_path, {'app/flexygram/glass/IosGlassConfig.java':'package app.flexygram.glass;public class IosGlassConfig{public static final int COMPOSER=2;public static boolean active(int surface){return false;}}', 'Probe.java': '''
class Canvas{boolean hardware,fail;Canvas(boolean h){hardware=h;}boolean isHardwareAccelerated(){return hardware;}}
class Rect{void set(int l,int t,int r,int b){}void inset(int x,int y){}void offset(int x,int y){}}
class Drawable{boolean isIosGlassSurface(int surface){return false;}int alpha=255,hides;void setBounds(int a,int b,int c,int d){}void setBounds(Rect r){}void draw(Canvas c){}void setAlpha(int a){alpha=a;hides++;}}
class Composer{boolean nativeDrawn,voice,send,compact=true;boolean isFlexyCompactPresentation(){return compact;}
 void setFlexyNativeGlassBackdropDrawn(boolean v){nativeDrawn=v;}void setFlexyVoiceBackdropDrawn(boolean v){voice=v;}void setFlexySendBackdropDrawn(boolean v){send=v;}}
class Channels{boolean isSignatureCompactPresentation(){return true;}}
class Base{protected void dispatchDraw(Canvas c){Host h=(Host)this;
 if(h.flexyComposer!=null&&h.drawInputBackground&&h.flexyComposer.compact){
  if(h.flexyComposer.nativeDrawn!=c.hardware||h.flexyComposer.voice!=c.hardware||h.flexyComposer.send!=c.hardware)throw new AssertionError("wrong capture ownership");}
 if(c.fail)throw new IllegalStateException("capture failed");}}
class Host extends Base{
 static int dp(int v){return v;}static final int INPUT_KEYBOARD_RADIUS=12;
 final Drawable underKeyboardBackgroundDrawable=new Drawable(),blurredBackgroundDrawable=new Drawable();
 final Drawable[] compactGlass={new Drawable(),new Drawable(),new Drawable(),new Drawable()};
 final boolean[] compactGlassDrawn=new boolean[4];final Rect tmpRect=new Rect();
 Composer flexyComposer=new Composer();Channels flexyChannels;
 float imeBottomInset,inputBubbleOffsetLeft,inputBubbleOffsetRight,bubbleInputTranlationY;int currentBlurredHeight,inputBubbleHeightRound;
 boolean flexyNativeGlassDrawn,flexyVoiceDrawn,flexySendDrawn,drawInputBackground=true,needDrawInAppKeyboard;
 int getMeasuredWidth(){return 400;}int getMeasuredHeight(){return 800;}
 void drawFlexyCompactBackground(Canvas c){if(c.hardware){flexyNativeGlassDrawn=flexyVoiceDrawn=flexySendDrawn=true;for(int i=0;i<4;i++){compactGlassDrawn[i]=true;compactGlass[i].alpha=255;}}}
 void drawSignatureChannelBackground(Canvas c){if(c.hardware){compactGlassDrawn[0]=true;compactGlass[0].alpha=255;}}
 DRAW
}
public class Probe{
 static void check(boolean v){if(!v)throw new AssertionError();}
 static void live(Host h){check(h.flexyNativeGlassDrawn&&h.flexyVoiceDrawn&&h.flexySendDrawn);check(h.flexyComposer.nativeDrawn&&h.flexyComposer.voice&&h.flexyComposer.send);for(Drawable d:h.compactGlass)check(d.alpha==255&&d.hides==0);for(boolean drawn:h.compactGlassDrawn)check(drawn);}
 public static void main(String[]args){Host h=new Host();Canvas screen=new Canvas(true),snapshot=new Canvas(false);
 h.dispatchDraw(screen);live(h);
 for(int i=0;i<1000;i++){h.dispatchDraw(snapshot);live(h);} // Menu stays open without requiring a live redraw.
 snapshot.fail=true;try{h.dispatchDraw(snapshot);throw new AssertionError();}catch(IllegalStateException expected){}live(h);
 snapshot.fail=false;h.dispatchDraw(screen);live(h);
 h.drawInputBackground=false;h.dispatchDraw(screen);check(!h.flexyComposer.nativeDrawn&&!h.flexyComposer.voice&&!h.flexyComposer.send);
 for(Drawable d:h.compactGlass)check(d.alpha==0&&d.hides==1); // Real policy changes still hide unused surfaces.
 Host channel=new Host();channel.flexyComposer=null;channel.flexyChannels=new Channels();channel.dispatchDraw(screen);
 int hides=channel.compactGlass[0].hides;channel.dispatchDraw(snapshot);check(channel.compactGlass[0].alpha==255&&channel.compactGlass[0].hides==hides);
 }}'''.replace('DRAW',draw)})


def test_child_background_cache_invalidates_only_when_ownership_changes(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/ChatActivityEnterView.java').read_text()
    setter=method(source,'public void setFlexyNativeGlassBackdropDrawn(')
    probe(tmp_path, {'Probe.java': '''public class Probe{
 boolean flexyNativeGlassBackdropDrawn;int invalidations;void invalidate(){invalidations++;}
 SETTER
 public static void main(String[]args){Probe p=new Probe();p.setFlexyNativeGlassBackdropDrawn(true);
 for(int i=0;i<1000;i++)p.setFlexyNativeGlassBackdropDrawn(true);
 if(p.invalidations!=1)throw new AssertionError("idle invalidation loop");
 p.setFlexyNativeGlassBackdropDrawn(false);if(p.invalidations!=2)throw new AssertionError("stale background");}
}'''.replace('SETTER',setter)})
