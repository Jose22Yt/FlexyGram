"""Actual production voice bounds/paint ownership; no device or visual acceptance claim."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_flexy_composer import ROOT, ENTER, CONTAINER, method_bodies

class IPhoneGlass(unittest.TestCase):
    def test_settled_voice_coordinates_and_display_list_ownership_edges(self):
        source=(ROOT/ENTER).read_text()
        methods='\n'.join(method_bodies(source,name)[0] for name in ('getFlexyVoiceBounds','setFlexyVoiceBackdropDrawn'))
        fixture='''
public class VoiceSurface {
 static final int VISIBLE=0;
 static float density=1;
 static int dp(float v){return Math.round(v*density);}
 static class RectF {float l,t,r,b; void set(float l,float t,float r,float b){this.l=l;this.t=t;this.r=r;this.b=b;}}
 static class V {
  float x,y,alpha=1,scale=1;int invalidations,visibility=VISIBLE;
  float getX(){return x;} float getY(){return y;} int getWidth(){return dp(44);}int getHeight(){return dp(44);}
  int getVisibility(){return visibility;}float getAlpha(){return alpha;}float getScaleX(){return scale;}float getScaleY(){return scale;}
  void invalidate(){invalidations++;}
 }
 V audioVideoButtonContainer=new V(),textFieldContainer=new V(),sendButtonContainer=new V(),expandStickersButton=new V();
 boolean flexyVoiceBackdropDrawn,presentation=true;int flexyInsetDp;
 boolean isFlexyCompactPresentation(){return presentation;}
 _METHODS_
 static void ok(boolean v){if(!v)throw new AssertionError("voice glass ownership/coordinates");}
 public static void main(String[] args){
  VoiceSurface s=new VoiceSurface();s.expandStickersButton.alpha=0;
  s.textFieldContainer.x=10;s.textFieldContainer.y=4;s.sendButtonContainer.x=20;s.sendButtonContainer.y=8;s.audioVideoButtonContainer.x=30;s.audioVideoButtonContainer.y=12;
  RectF out=new RectF();
  for(float scale:new float[]{1,1.5f,2,2.625f,3,4}){density=scale;
   for(int inset:new int[]{0,2,4}){s.flexyInsetDp=inset;ok(s.getFlexyVoiceBounds(out));
    ok(out.l==60+dp(inset)&&out.t==24+dp(inset));ok(out.r-out.l==dp(44)-2*dp(inset));ok(out.b-out.t==dp(44)-2*dp(inset));
   }
  }
  for(int i=0;i<10000;i++)s.setFlexyVoiceBackdropDrawn(true);
  ok(s.audioVideoButtonContainer.invalidations==1);
  for(int i=0;i<10000;i++)s.setFlexyVoiceBackdropDrawn(false);
  ok(s.audioVideoButtonContainer.invalidations==2);
  s.presentation=false;ok(!s.getFlexyVoiceBounds(out));s.presentation=true;
  s.audioVideoButtonContainer.alpha=.5f;ok(!s.getFlexyVoiceBounds(out));s.audioVideoButtonContainer.alpha=1;
  s.audioVideoButtonContainer.scale=.8f;ok(!s.getFlexyVoiceBounds(out));s.audioVideoButtonContainer.scale=1;
  s.sendButtonContainer.scale=.79f;ok(!s.getFlexyVoiceBounds(out));s.sendButtonContainer.scale=1;
  s.sendButtonContainer.alpha=.5f;ok(!s.getFlexyVoiceBounds(out));s.sendButtonContainer.alpha=1;
  s.expandStickersButton.alpha=.5f;ok(!s.getFlexyVoiceBounds(out));s.expandStickersButton.alpha=0;
  s.audioVideoButtonContainer.visibility=8;ok(!s.getFlexyVoiceBounds(out));
  System.out.println("PASS");
 }
}
'''.replace('_METHODS_',methods)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'VoiceSurface.java';p.write_text(fixture)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(p)],check=True)
            self.assertIn('PASS',subprocess.check_output(['java','-cp',tmp,'VoiceSurface'],text=True))

    def test_single_backdrop_and_single_ownership_publication_per_parent_frame(self):
        source=(ROOT/CONTAINER).read_text()
        draw=method_bodies(source,'drawFlexyCompactBackground')[0]
        self.assertEqual(draw.count('blurredBackgroundDrawable.draw(canvas)'),1)
        self.assertIn('flexyMask.addRoundRect(flexyVoice',draw)
        self.assertIn('canvas.drawRoundRect(flexyVoice, radius, radius, flexySurface)',draw)
        self.assertIn('canvas.drawRoundRect(flexyVoice, radius, radius, flexyPearl)',draw)
        dispatch=next(body for body in method_bodies(source,'dispatchDraw') if 'drawFlexyCompactBackground(canvas)' in body)
        self.assertEqual(dispatch.count('setFlexyVoiceBackdropDrawn('),1)
        self.assertLess(dispatch.index('flexyVoiceDrawn = false'),dispatch.index('drawFlexyCompactBackground(canvas)'))
        self.assertLess(dispatch.index('setFlexyVoiceBackdropDrawn('),dispatch.index('super.dispatchDraw(canvas)'))
        for token in ('new ', 'requestLayout(', 'ValueAnimator', 'ObjectAnimator'):
            self.assertNotIn(token,draw)
