"""Exact PlayerSheet transition protocols; playback, palette and layout are explicit doubles."""
def method(source,signature):
 start=source.index(signature);i=source.index('{',start);depth=1;j=i+1
 while depth:
  if source[j]=='{':depth+=1
  elif source[j]=='}':depth-=1
  j+=1
 return source[start:j]

def write(put,root):
 s=(root/'TMessagesProj/src/main/java/app/exteraless/player/PlayerSheet.java').read_text()
 methods='\n'.join(method(s,n)for n in ['    protected void onCustomBackCancelled()', '    private void cancelBackAnimator()', '    private void startMorph(', '    private void setLyricsMode(', '    protected boolean onCustomOpenAnimation()'])
 put('PlayerMotionProbe.java','''import android.animation.*;import android.view.*;import android.widget.*;import org.telegram.ui.Components.CubicBezierInterpolator;import org.telegram.messenger.BuildConfig;
public class PlayerMotionProbe extends FrameLayout {
 final View root=this;View cover,titleRow,lyricsPanel;public boolean closing,backPreview,lyricsMode;public float backProgress,morphProgress=-1,lyricsFraction,morphToRadius;final android.graphics.RectF morphTo=new android.graphics.RectF();public int morphBarsState=-1,clears,morphs,barUpdates,lyricLoads,restores;
 app.flexygram.motion.FlexyMotionAnimator backAnimator,morphAnimator,lyricsAnimator,elevationAnimator;
 static final android.animation.TimeInterpolator EMPHASIZED=new android.view.animation.PathInterpolator(.2f,0,0,1);
 static class Mini {boolean hidden;void setTransitionHidden(boolean v){hidden=v;}}public final Mini miniSource=new Mini();
 static class LyricButton {void setActive(boolean a,boolean b){}void setRadius(int a,boolean b){}}final LyricButton lyricsButton=new LyricButton();
 static class Lyrics {long position;void setPosition(long p){position=p;}}final Lyrics lyricsView=new Lyrics();
 static class MessageObject {float audioProgress;float getDuration(){return 180;}}MessageObject current;
 PlayerMotionProbe(android.content.Context c){super(c);cover=new View(c);cover.setElevation(8);addView(cover);titleRow=new View(c);lyricsPanel=new View(c);}
 boolean prepareMorph(boolean hide){return true;}void restoreMorphCover(){restores++;}void onOpenAnimationEnd(){}static class Delegate{void onOpenAnimationEnd(){}}Delegate delegate;
 static int dp(float x){return (int)x;}static float clamp01(float x){return Math.max(0,Math.min(1,x));}
 void applyBackPreview(){}void clearMorph(){clears++;morphProgress=-1;}void applySystemBars(boolean light){barUpdates++;}void applyMorph(){morphs++;}void loadLyrics(){lyricLoads++;}void setLyricsFraction(float v){lyricsFraction=v;}
 public void morph(float from,float to,long d,Runnable end){startMorph(from,to,d,end);}public void lyrics(boolean value,boolean animated){setLyricsMode(value,animated);}public void cancelBack(){cancelBackAnimator();}public void detachProtocol(){cancelBackAnimator();if(morphAnimator!=null){morphAnimator.removeAllListeners();morphAnimator.cancel();morphAnimator=null;}if(lyricsAnimator!=null){lyricsAnimator.removeAllListeners();lyricsAnimator.cancel();lyricsAnimator=null;}if(elevationAnimator!=null){elevationAnimator.removeAllListeners();elevationAnimator.cancel();elevationAnimator=null;}}
'''+methods+'}')
