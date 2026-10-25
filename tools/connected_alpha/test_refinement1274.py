"""Corrective geometry and exact preservation over approved Alpha1273 + Work2 Studio."""
import subprocess,tempfile,unittest
from pathlib import Path
from refinement1274_contract import ROOT,BASE,PATCH,restore
class Refinement(unittest.TestCase):
 def test_every_corrective_patch_reverses_and_unreviewed_mutations_fail(self):
  paths=[s[6:].decode()for s in PATCH.read_bytes().splitlines()if s.startswith(b'+++ b/')]
  self.assertGreater(len(paths),10)
  for path in paths:
   actual=(ROOT/path).read_bytes()
   before=subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True)
   self.assertEqual(restore(path,actual),before.stdout if before.returncode==0 else b'',path)
   with self.assertRaises(ValueError,msg=path):restore(path,actual+b'\nUNREVIEWED\n')
 def test_preview_fix_auth_and_audio_engine_are_byte_exact_to_physically_accepted_1273(self):
  for path in ['org/telegram/ui/ActionBar/ActionBarLayout.java','org/telegram/ui/DialogsActivity.java','org/telegram/ui/LoginActivity.java','org/telegram/messenger/MediaController.java','org/telegram/messenger/ImageReceiver.java']:
   path='TMessagesProj/src/main/java/'+path
   self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show','751c926d91acd536d96b427af5f34f2fe6bedbc4:'+path],cwd=ROOT))
 def test_real_geometry_handles_counter_modes_rtl_and_compact_surfaces(self):
  rect='package android.graphics;public class RectF{public float left,top,right,bottom;public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}public float width(){return right-left;}public float height(){return bottom-top;}public float centerX(){return(left+right)/2;}public void offset(float x,float y){left+=x;right+=x;top+=y;bottom+=y;}}'
  code='''import app.flexygram.header.HeaderGeometry;class Probe{public static void main(String[]args){int cases=0;for(float d:new float[]{.75f,1,2,3,4})for(int w:new int[]{240,320,401,600})for(boolean rtl:new boolean[]{false,true})for(int mode=0;mode<3;mode++)for(int digits:new int[]{0,1,2,3,4}){
 int width=Math.round(w*d);HeaderGeometry g=new HeaderGeometry();g.update(width,24*d,44*d,digits*8*d,d,rtl,mode);
 if(g.title.centerX()!=width/2f||Math.abs(g.back.height()-g.avatar.height())>.001f||Math.abs(g.title.height()-g.avatar.height())>.001f)throw new AssertionError("center/height");
 if(g.countVisible){if(mode==0||digits==0||g.badge.left<g.back.left||g.badge.right>g.back.right+.001f)throw new AssertionError("counter bounds");if(g.separateCount!=(mode==2))throw new AssertionError("style");}
 if(rtl?g.title.right>g.back.left||g.avatar.right>g.title.left:g.back.right>g.title.left||g.title.right>g.avatar.left)throw new AssertionError("overlap");cases++;}
 if(HeaderGeometry.height(401,21,17,1,false)!=46||HeaderGeometry.height(401,18,14,1,true)!=40)throw new AssertionError("normal/compact");System.out.println(cases);}}'''
  with tempfile.TemporaryDirectory()as d:
   tmp=Path(d);p=tmp/'android/graphics/RectF.java';p.parent.mkdir(parents=True);p.write_text(rect);(tmp/'Probe.java').write_text(code)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(p),str(tmp/'Probe.java'),str(ROOT/'TMessagesProj/src/main/java/app/flexygram/header/HeaderGeometry.java')],check=True,capture_output=True)
   result=subprocess.check_output(['java','-cp',d,'Probe'],text=True);self.assertEqual(result.strip(),'600')
 def test_no_public_apk_upload_on_integration_pr(self):
  import yaml
  data=yaml.safe_load((ROOT/'.github/workflows/pr.yml').read_text())
  self.assertIn("github.head_ref != 'integration/alpha1274-signature-refinement-studio'",data['jobs']['build']['if'])
  checks=yaml.safe_load((ROOT/'.github/workflows/refinement1274.yml').read_text())
  self.assertIn('studio_native',str(checks));self.assertNotIn('*.apk',str(checks))

 def test_current_release_identity_is1274_and_all_original_signing_guards_remain(self):
  import re,yaml
  gradle=(ROOT/'TMessagesProj/build.gradle').read_text()
  self.assertEqual(re.search(r'def verCode = (\d+)',gradle)[1],'1274')
  self.assertEqual(restore('TMessagesProj/build.gradle',gradle.encode()),subprocess.check_output(['git','show',BASE+':TMessagesProj/build.gradle'],cwd=ROOT))
  flow=(ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text()
  self.assertIn('--expected-version-code 1274',flow)
  self.assertIn("c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c",flow)
  self.assertIn("data['elf_count'] != 96",flow)
  self.assertIn('assembleConnectedAlpha',flow)
  for step in yaml.safe_load(flow)['jobs']['build-arm64']['steps']:self.assertNotIn('upload-artifact',step.get('uses',''))
 def test_real_outline_policy_preserves_chroma_and_pearl_is_tinted_not_flat_white(self):
  code="""import app.flexygram.bubbles.BubbleOutline;class OutlineProbe{public static void main(String[]args){int cases=0;for(int c:new int[]{0xff2255aa,0xff8833bb,0xff228844,0xffaaaaaa})for(boolean dark:new boolean[]{false,true})for(int style:new int[]{0,1})for(int intensity:new int[]{0,55,100}){int out=BubbleOutline.color(c,dark,style,intensity);int r=(out>>>16)&255,g=(out>>>8)&255,b=out&255;int cr=(c>>>16)&255,cg=(c>>>8)&255,cb=c&255;if(Integer.compare(r,g)!=Integer.compare(cr,cg)||Integer.compare(g,b)!=Integer.compare(cg,cb))throw new AssertionError("chroma");if(style==1&&(out&0xffffff)==0xffffff)throw new AssertionError("flat white");if(out!=BubbleOutline.color(c,dark,style,intensity))throw new AssertionError("unstable");cases++;}if(BubbleOutline.palette(0xff22aa44,0,0,0)!=0xff22aa44)throw new AssertionError("flat palette");System.out.println(cases);}}"""
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'OutlineProbe.java';p.write_text(code)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(p),str(ROOT/'TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleOutline.java')],check=True,capture_output=True)
   self.assertEqual(subprocess.check_output(['java','-cp',d,'OutlineProbe'],text=True).strip(),'48')
