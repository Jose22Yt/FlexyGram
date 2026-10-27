"""Actual v3 geometry/curve against the validated v1 three-piece layout; no physical/GPU claim."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'TMessagesProj/src/main/java/app/flexygram/header/fusion'
class FusionV3(unittest.TestCase):
 def test_extended_tail_preserves_text_controls_and_is_nearly_invisible_at_the_name(self):
  old=subprocess.check_output(['git','show','38e677d60847e117ede1c25731f7b6c4fd2970e2:'+str((FOLDER/'SignatureFusionGeometry.java').relative_to(ROOT))],cwd=ROOT,text=True).replace('SignatureFusionGeometry','BaselineFusionGeometry')
  runner='''package app.flexygram.header.fusion;class Probe{
  static void same(float x,float y){if(Math.abs(x-y)>.001f)throw new AssertionError(x+" != "+y);}
  public static void main(String[]args){int n=0;for(int width=240;width<=840;width+=11)for(float d:new float[]{.75f,1,1.25f,1.5f,2,3,4})for(boolean rtl:new boolean[]{false,true})for(boolean call:new boolean[]{false,true}){
  var old=BaselineFusionGeometry.calculate(width*d,d,rtl,call);var g=SignatureFusionGeometry.calculate(width*d,d,rtl,call);
  if(g.fits!=old.fits)throw new AssertionError();same(g.text.left,old.text.left);same(g.text.right,old.text.right);same(g.text.top,old.text.top);same(g.text.bottom,old.text.bottom);same(g.back.left,old.back.left);same(g.back.right,old.back.right);same(g.actions.left,old.actions.left);same(g.actions.right,old.actions.right);same(g.center.left,old.center.left);same(g.center.right,old.center.right);
  if(g.fits){float name=rtl?g.text.right:g.text.left;float t=(name-g.fadeStartX)/(g.fadeEndX-g.fadeStartX);float opacity=SignatureFusionFade.opacityAt(t);if(opacity>.05f||opacity<=0||Math.abs(g.fadeEndX-name)<4.9f*d||g.portrait.width()>80.01f*d)throw new AssertionError("name fade "+opacity);if(g.portrait.width()<=old.portrait.width())throw new AssertionError();n++;}}
  float previous=1;for(int i=0;i<=10000;i++){float alpha=SignatureFusionFade.opacityAt(i/10000f);if(alpha<0||alpha>previous)throw new AssertionError();previous=alpha;}
  for(int i=0;i<SignatureFusionFade.LTR_STOPS.length;i++){int reverse=SignatureFusionFade.LTR_STOPS.length-1-i;same(SignatureFusionFade.LTR_STOPS[i],1-SignatureFusionFade.RTL_STOPS[reverse]);if(SignatureFusionFade.LTR_COLORS[i]!=SignatureFusionFade.RTL_COLORS[reverse])throw new AssertionError();}
  System.out.println("PASS extended name fade, mirrored curve, unchanged text/control layout: "+n);}}
  '''
  with tempfile.TemporaryDirectory()as tmp:
   a=Path(tmp)/'BaselineFusionGeometry.java';a.write_text(old);b=Path(tmp)/'Probe.java';b.write_text(runner)
   r=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(a),str(b),str(FOLDER/'SignatureFusionGeometry.java'),str(FOLDER/'SignatureFusionFade.java')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run(['java','-cp',tmp,'app.flexygram.header.fusion.Probe'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertIn('PASS extended name fade',r.stdout)
