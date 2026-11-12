"""Execute production reaction timing/handoff/lifecycle logic with explicit UI doubles."""
from pathlib import Path
from test_render_work_reuse import probe,JAVA
from test_composer_layout import method
R=JAVA/'app/flexygram/reactions'
OVERLAY=JAVA/'org/telegram/ui/Components/Reactions/ReactionsEffectOverlay.java'


def test_motion_duration_is_refresh_independent_and_endpoints_are_continuous(tmp_path):
    probe(tmp_path,{
        'Probe.java':'''import app.flexygram.reactions.ReactionMotion;
public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){
 for(int hz:new int[]{30,60,90,120,144}){ReactionMotion m=new ReactionMotion();float progress=0;long now=1000;int frames=0;
 while(progress<1&&frames<1000){now=1000+Math.round(frames*1000.0/hz);progress=ReactionMotion.advance(progress,m.tick(now),350);frames++;}
 // 30 Hz is intentionally capped at 32 ms after a missed/vsync interval.
 check(progress==1);if(hz>=60)check(now-1000>=350&&now-1000<=350+Math.ceil(1000.0/hz));}
 ReactionMotion m=new ReactionMotion();check(m.tick(1000)==0);check(m.tick(2000)==32);check(m.tick(1900)==0);check(m.tick(2008)==8);m.reset();check(m.tick(3000)==0);
 check(ReactionMotion.ease(0)==0&&ReactionMotion.ease(1)==1);float previous=0;
 for(int i=0;i<=10000;i++){float p=i/10000f,actual=ReactionMotion.ease(p);check(actual>=previous&&actual>=0&&actual<=1);check(ReactionMotion.lift(p,20)>=0&&ReactionMotion.lift(p,20)<=20);previous=actual;}
 check(ReactionMotion.lift(0,20)==0&&ReactionMotion.lift(1,20)==0);check(ReactionMotion.ease(.001f)<.000001f&&1-ReactionMotion.ease(.999f)<.000001f);
 }}'''},[R/'ReactionMotion.java'])


def test_handoff_never_hides_a_pending_or_unrendered_icon(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.reactions.ReactionIconHandoff;
public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){
 ReactionIconHandoff h=new ReactionIconHandoff();check(!h.hidesIcon());h.update(false,true);check(!h.hidesIcon());h.update(true,false);check(!h.hidesIcon());h.update(true,true);check(h.hidesIcon());h.update(false,true);check(!h.hidesIcon());h.update(true,true);h.finish();check(!h.hidesIcon());h.update(true,true);check(!h.hidesIcon());
 }}'''},[R/'ReactionIconHandoff.java'])


def test_retiring_overlay_cannot_clear_newer_reactions_or_strand_source_icons(tmp_path):
    source=OVERLAY.read_text()
    methods='\n'.join(method(source,s)for s in ['private void releaseAvatarParticles()','private void removeCurrentView()','public static void dismissByFragment(','public static boolean isPlaying(int account,','public static boolean isPlaying(int messageId,','private void dismiss()','private static void retirePreviousFor(']).replace('ReactionsEffectOverlay','Probe')
    probe(tmp_path,{'Probe.java':'''import java.util.*;import app.flexygram.reactions.ReactionIconHandoff;
public class Probe{
 static class BaseFragment{}static class View{float alpha=1;int invalidations;void invalidate(){invalidations++;}void setAlpha(float a){alpha=a;}}
 static class Animator{Animator setListener(Object o){return this;}void cancel(){}}
 static class WindowView extends View{int cancels,frames;void removeCallbacks(Runnable r){cancels++;}Animator animate(){return new Animator();}void postInvalidateOnAnimation(){frames++;}}
 static class WindowManager{boolean fail;void removeView(WindowView v){if(fail)throw new RuntimeException("already detached");}}static class AndroidUtilities{static void removeFromParent(WindowView v){}}
 static class Holder{Object currentReaction;View enterImageView=new View(),pressedBackupImageView=new View();}
 static class ReactionsLayoutInBubble{static class VisibleReaction{}}
 static final int ONLY_MOVE_ANIMATION=2,LONG_ANIMATION=0,SHORT_ANIMATION=1;int animationType=LONG_ANIMATION,currentAccount=1,messageId=5;long groupId;
 static Probe currentOverlay,currentShortOverlay;static ArrayList<Probe> activeOverlays=new ArrayList<>();
 static class Receiver{int detaches;void onDetachedFromWindow(){detaches++;}}static class AvatarParticle{Receiver imageReceiver=new Receiver();}
 ArrayList<AvatarParticle> avatars=new ArrayList<>();boolean avatarsAttached;
 boolean removed,useWindow,sourceIconHidden,started,dismissed,isStories;float sourceEnterAlpha=.6f,sourcePressedAlpha=.2f;
 Probe companion;Holder holderView;View cell=new View();BaseFragment baseFragment;WindowView windowView=new WindowView();WindowManager windowManager=new WindowManager();Runnable expireOverlay=()->{};
 ReactionIconHandoff iconHandoff=new ReactionIconHandoff();ReactionsLayoutInBubble.VisibleReaction reaction=new ReactionsLayoutInBubble.VisibleReaction();
 METHODS
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){
 Probe old=new Probe(),newer=new Probe();currentOverlay=newer;old.removeCurrentView();check(currentOverlay==newer&&old.removed);int canceled=old.windowView.cancels;old.removeCurrentView();check(old.windowView.cancels==canceled);
 currentOverlay=newer;newer.started=true;check(!isPlaying(1,newer.cell,5,0,newer.reaction));newer.iconHandoff.update(true,true);check(isPlaying(1,newer.cell,5,0,newer.reaction));check(!isPlaying(2,newer.cell,5,0,newer.reaction));check(!isPlaying(1,new View(),5,0,newer.reaction));newer.dismiss();check(!isPlaying(1,newer.cell,5,0,newer.reaction)&&newer.windowView.frames==1);
 Probe retired=new Probe();retired.avatarsAttached=true;retired.useWindow=true;retired.windowManager.fail=true;AvatarParticle avatar=new AvatarParticle();retired.avatars.add(avatar);retired.removeCurrentView();retired.removeCurrentView();check(retired.avatars.isEmpty()&&!retired.avatarsAttached&&avatar.imageReceiver.detaches==1);
 Probe p=new Probe();p.holderView=new Holder();p.holderView.currentReaction=p.reaction;p.sourceIconHidden=true;p.holderView.enterImageView.alpha=0;p.removeCurrentView();check(p.holderView.enterImageView.alpha==.6f&&p.holderView.pressedBackupImageView.alpha==.2f);
 Probe reused=new Probe();reused.holderView=new Holder();reused.sourceIconHidden=true;reused.holderView.currentReaction=new Object();reused.holderView.enterImageView.alpha=.8f;reused.removeCurrentView();check(reused.holderView.enterImageView.alpha==.8f);
 // Removing a parent also retires its unstarted companion; reverse traversal
 // must remain valid when more than one element disappears in one iteration.
 BaseFragment f=new BaseFragment();Probe parent=new Probe(),child=new Probe(),other=new Probe();parent.baseFragment=child.baseFragment=f;parent.companion=child;activeOverlays.add(child);activeOverlays.add(parent);activeOverlays.add(other);currentOverlay=other;dismissByFragment(f);check(parent.removed&&child.removed&&activeOverlays.size()==1&&currentOverlay==other);
 // Fading overlays have already lost the global pointer. They still retire
 // before a new reaction can reuse/hide the same popup source view.
 Probe fading=new Probe(),shortEffect=new Probe();fading.baseFragment=shortEffect.baseFragment=f;fading.dismissed=true;shortEffect.animationType=SHORT_ANIMATION;activeOverlays.add(fading);activeOverlays.add(shortEffect);retirePreviousFor(f,LONG_ANIMATION);check(fading.removed&&!shortEffect.removed&&!other.removed);
 }}'''.replace('METHODS',methods)},[R/'ReactionIconHandoff.java'])


def test_completed_pose_draws_before_cleanup_and_waiting_has_a_bounded_lifetime():
    source=OVERLAY.read_text();draw=method(source,'protected void dispatchDraw(Canvas canvas)')
    assert draw.index('ReactionMotion.advance(animateInProgress')<draw.index('super.dispatchDraw(canvas);',draw.index('float animateInProgressX'))
    pose_draw=draw.index('super.dispatchDraw(canvas);',draw.index('float animateInProgressX'))
    assert pose_draw<draw.index('if (ReactionsEffectOverlay.this.animateOutProgress >= 1f && !completionDispatched)')
    assert 'if (!started) return;' in draw
    assert 'postDelayed(expireOverlay,5000)' in source
    assert 'windowView.removeCallbacks(expireOverlay)' in source
    assert 'avatars.size()>=4' in source
    assert 'advanceAvatarExit(i, frameMs, isLeft)' in draw
    assert 'particle.imageReceiver.onDetachedFromWindow()' in method(source,'private boolean advanceAvatarExit(')
    assert 'float flightFromX=fromX-(isStories?0:overlayLocation[0])' in draw
    assert '(reactionButton == null || reactionButton.drawingImageRect.width() <= 0' in draw
    assert 'if(!landingStarted){landingStarted=true;landingX=x;landingY=y;landingScale=scale;}' in draw
    for old in ['animateInProgress += 16','animateOutProgress += 16','dismissProgress += 16','particle.progress += 16']:
        assert old not in draw


def test_inline_fade_waits_for_a_decoded_completed_animation():
    source=(JAVA/'org/telegram/ui/Components/Reactions/ReactionsLayoutInBubble.java').read_text()
    fade=method(source,'private void drawImage(Canvas canvas, Rect bounds, float alpha)')
    assert 'ReactionMotion.elapsed(inlineFadeTime,now)' in fade
    assert 'getLottieAnimation().hasBitmap()\n                                && !imageReceiver2' in fade
    assert 'getCurrentFrame() >= imageReceiver2.getLottieAnimation().getFramesCount()-1' in fade
    assert '16f / 200' not in fade


def test_selector_release_does_not_fight_press_growth_or_replace_another_animator():
    source=(JAVA/'org/telegram/ui/Components/ReactionsContainerLayout.java').read_text()
    draw=method(source,'protected void dispatchDraw(Canvas canvas)')
    assert 'selectorMotion.tick(android.os.SystemClock.uptimeMillis())' in draw
    assert 'cancelPressedAnimation == null && !clicked' in draw
    assert 'pressedProgress += dt /' in draw
    cancel=method(source,'private void cancelPressed()')
    assert 'if(cancelPressedAnimation!=null)return;' in cancel
    assert 'if(cancelPressedAnimation!=valueAnimator)return;' in cancel
    assert 'if(cancelPressedAnimation!=animation)return;' in cancel


def test_decoding_placeholder_is_not_a_frame_and_rebinding_unregisters_the_old_emoji(tmp_path):
    source=OVERLAY.read_text()
    ready=method(source,'private boolean frameReady(')
    setter=method(source,'public void setAnimatedReactionDrawable(')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class Lottie{boolean bitmap;boolean hasBitmap(){return bitmap;}}
 static class ImageReceiver{Lottie lottie;boolean loaded,thumb;Lottie getLottieAnimation(){return lottie;}boolean hasImageLoaded(){return loaded;}}
 static class AnimatedEmojiDrawable{int removes,adds;void removeView(Object v){removes++;}void addView(Object v){adds++;}}
 AnimatedEmojiDrawable animatedEmojiDrawable;boolean attached=true,hasDrawnFrame=true,wasPlaying=true;
 READY
 SETTER
 public static void main(String[]args){Probe p=new Probe();ImageReceiver r=new ImageReceiver();r.thumb=true;if(p.frameReady(r))throw new AssertionError("placeholder hides native icon");r.lottie=new Lottie();if(p.frameReady(r))throw new AssertionError("undecoded lottie");r.lottie.bitmap=true;if(!p.frameReady(r))throw new AssertionError();AnimatedEmojiDrawable old=new AnimatedEmojiDrawable(),next=new AnimatedEmojiDrawable();p.animatedEmojiDrawable=old;p.setAnimatedReactionDrawable(next);if(old.removes!=1||next.removes!=0||next.adds!=1||p.hasDrawnFrame||p.wasPlaying)throw new AssertionError("stale drawable attached");p.setAnimatedReactionDrawable(null);if(next.removes!=1)throw new AssertionError();}
 }'''.replace('READY',ready).replace('SETTER',setter)},[])


def test_avatar_exit_releases_exact_endpoint_siblings_and_nested_teardown(tmp_path):
    source=OVERLAY.read_text()
    methods='\n'.join(method(source,s) for s in [
        'private boolean advanceAvatarExit(', 'private void releaseAvatarParticles()'])
    probe(tmp_path, {'Probe.java': '''import java.util.*;import app.flexygram.reactions.ReactionMotion;
public class Probe{
 static class Receiver{int detaches;Runnable callback;void onDetachedFromWindow(){detaches++;Runnable next=callback;callback=null;if(next!=null)next.run();}}
 static class AvatarParticle{float outProgress;Receiver imageReceiver=new Receiver();}
 ArrayList<AvatarParticle> avatars=new ArrayList<>();boolean avatarsAttached;
 METHODS
 static void check(boolean v){if(!v)throw new AssertionError();}
 AvatarParticle add(float out){AvatarParticle p=new AvatarParticle();p.outProgress=out;avatars.add(p);return p;}
 public static void main(String[]args){
  Probe p=new Probe();p.avatarsAttached=true;AvatarParticle waiting=p.add(0f);
  check(!p.advanceAvatarExit(0,16,false)&&waiting.outProgress==0&&waiting.imageReceiver.detaches==0);
  check(!p.advanceAvatarExit(0,16,true)&&waiting.outProgress>0&&waiting.outProgress<1);
  p.releaseAvatarParticles();check(waiting.imageReceiver.detaches==1);p.releaseAvatarParticles();check(waiting.imageReceiver.detaches==1);
  // The real clamped clock reaches exactly 1, never greater than 1.
  p.avatarsAttached=true;ArrayList<AvatarParticle> expired=new ArrayList<>();for(int i=0;i<4;i++)expired.add(p.add(.98f));
  int drawn=0;for(int i=0;i<p.avatars.size();i++){if(p.advanceAvatarExit(i,16,true)){i--;continue;}drawn++;}
  check(p.avatars.isEmpty()&&drawn==0);for(AvatarParticle a:expired)check(a.outProgress==1&&a.imageReceiver.detaches==1);
  AvatarParticle terminal=p.add(1);check(p.advanceAvatarExit(0,0,false)&&terminal.imageReceiver.detaches==1);
  // Unattached, queued overlays drop references without detaching unregistered receivers.
  p.avatarsAttached=false;AvatarParticle queued=p.add(.5f);p.releaseAvatarParticles();check(p.avatars.isEmpty()&&queued.imageReceiver.detaches==0);
  // Receiver cleanup can synchronously trigger parent teardown. Each owner is released once.
  p.avatarsAttached=true;AvatarParticle a=p.add(.98f),b=p.add(.5f),c=p.add(.5f);a.imageReceiver.callback=p::releaseAvatarParticles;
  check(p.advanceAvatarExit(0,16,true));check(p.avatars.isEmpty()&&!p.avatarsAttached);
  check(a.imageReceiver.detaches==1&&b.imageReceiver.detaches==1&&c.imageReceiver.detaches==1);
  p.releaseAvatarParticles();check(a.imageReceiver.detaches==1&&b.imageReceiver.detaches==1&&c.imageReceiver.detaches==1);
 }
}'''.replace('METHODS',methods)},[R/'ReactionMotion.java'])


def test_overlay_draw_updates_owner_field_without_capturing_a_mutable_constructor_argument(tmp_path):
    import re
    source=OVERLAY.read_text()
    constructor=re.search(r'public ReactionsEffectOverlay\([^\n]+\) \{',source).group(0)
    constructor=constructor.replace('ReactionsEffectOverlay','Probe')
    assignment=re.search(r'this\.cell\s*=\s*\w+;',source).group(0)
    draw=method(source,'protected void dispatchDraw(Canvas canvas)')
    # Compile the real constructor declaration and both owner updates inside an
    # anonymous class. Moving just the draw body to a flat probe hid the CI error.
    updates=re.findall(r'(?:if\(!isStories\))?cell\s*=\s*drawingCell;',draw)
    assert len(updates)==2
    probe(tmp_path, {'Probe.java': '''
class Context{}class BaseFragment{}class ReactionsContainerLayout{}class View{}
class ReactionsLayoutInBubble{static class VisibleReaction{}}
public class Probe{
 View cell,next;Runnable draw;
 CONSTRUCTOR
  ASSIGNMENT
  draw=new Runnable(){public void run(){View drawingCell=next;UPDATES}};
 }
 public static void main(String[]args){
  View original=new View(),replacement=new View();
  Probe p=new Probe(null,null,null,original,null,0,0,null,0,0,false);
  if(p.cell!=original)throw new AssertionError("source owner lost");
  p.next=replacement;p.draw.run();if(p.cell!=replacement)throw new AssertionError("recycled owner not updated");
  View next=new View();p.next=next;p.draw.run();if(p.cell!=next)throw new AssertionError("stale owner captured");
 }
}'''.replace('CONSTRUCTOR',constructor).replace('ASSIGNMENT',assignment).replace('UPDATES','\n'.join(updates))}, [])
