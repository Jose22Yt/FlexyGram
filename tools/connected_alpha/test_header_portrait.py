"""Exercise real retained Header4 geometry; full Android tests are separate."""
from pathlib import Path
import subprocess, tempfile, unittest
ROOT=Path(__file__).resolve().parents[2]
class PortraitGeometry(unittest.TestCase):
 def test_equal_visual_height_circular_photo_and_native_targets(self):
  probe='''import app.flexygram.header.fusion.SignatureFusionGeometry;
public class PortraitProbe {
 static void check(boolean v){if(!v)throw new AssertionError();}
 static void close(float a,float b){check(Math.abs(a-b)<.01f);}
 public static void main(String[] args){
  var g=new SignatureFusionGeometry.Layout();Object photo=g.portrait,more=g.more;
  for(int i=0;i<20000;i++){
   float d=1+(i%4)*.5f,w=(240+i%561)*d;boolean rtl=(i&1)!=0,call=(i&2)!=0;
   check(g==SignatureFusionGeometry.updatePortrait(g,w,d,rtl,call));
   check(photo==g.portrait&&more==g.more&&g.mattePortrait);
   close(g.portrait.width(),g.portrait.height());close(g.center.height(),g.backVisual.height());
   close(g.center.height(),g.moreVisual.height());if(call)close(g.center.height(),g.callVisual.height());
   close(48*d,g.more.width());if(call)close(48*d,g.call.width());
   close(g.center.centerY(),g.moreVisual.centerY());close(g.center.centerY(),g.backVisual.centerY());
   if(g.fits){check(g.portrait.left>=g.center.left&&g.portrait.right<=g.center.right);
    check(g.text.left>=g.center.left&&g.text.right<=g.center.right&&g.text.width()>=48*d);
    check(rtl?g.text.right<g.portrait.left:g.text.left>g.portrait.right);
    check(g.center.left>=Math.min(g.back.right,g.more.right));
   }
   SignatureFusionGeometry.update(g,w,d,rtl,call);check(!g.mattePortrait);
  }
  System.out.println("PASS 20000 portrait layouts, retained objects and native targets");
 }}'''
  with tempfile.TemporaryDirectory() as folder:
   source=Path(folder)/'PortraitProbe.java';source.write_text(probe)
   path=ROOT/'TMessagesProj/src/main/java/app/flexygram/header/fusion'
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',folder,str(path/'SignatureFusionGeometry.java'),str(path/'SignatureFusionFade.java'),str(source)],check=True,capture_output=True)
   self.assertIn('PASS 20000',subprocess.check_output(['java','-cp',folder,'PortraitProbe'],text=True))
if __name__=='__main__':unittest.main()
