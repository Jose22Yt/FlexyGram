"""Approved geometry executed unchanged, plus reused production layout differential checks."""
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class FusionGeometry(unittest.TestCase):
 def test_reference_geometry_and_reused_layout_match(self):
  production=ROOT/'TMessagesProj/src/main/java/app/flexygram/header/fusion/SignatureFusionGeometry.java'
  fixture=ROOT/'tools/connected_alpha/header_visual/SignatureFusionGeometryTest.java'
  probe="""import app.flexygram.header.fusion.SignatureFusionGeometry;class FusionReuse {
   public static void main(String[] args){var retained=new SignatureFusionGeometry.Layout();Object back=retained.back,text=retained.text,portrait=retained.portrait;
   for(int i=0;i<20000;i++){float width=240+i%401,density=1+(i%4)*.5f;boolean rtl=(i&1)!=0,call=(i&2)!=0;
    var expected=SignatureFusionGeometry.calculate(width*density,density,rtl,call);var actual=SignatureFusionGeometry.update(retained,width*density,density,rtl,call);
    if(actual!=retained||actual.back!=back||actual.text!=text||actual.portrait!=portrait||actual.fits!=expected.fits||actual.text.left!=expected.text.left||actual.center.right!=expected.center.right||actual.call.width()!=expected.call.width()||actual.fadeStartX!=expected.fadeStartX)throw new AssertionError();}
   for(float invalid:new float[]{0,-1,Float.NaN,Float.POSITIVE_INFINITY}){try{SignatureFusionGeometry.update(retained,401,invalid,false,true);throw new AssertionError();}catch(IllegalArgumentException ok){}}
   System.out.println("PASS 20000 reused layouts; original reference geometry; no new layout/rects");}}
  """
  with tempfile.TemporaryDirectory()as tmp:
   source=Path(tmp)/'FusionReuse.java';source.write_text(probe)
   result=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(production),str(production.with_name('SignatureFusionFade.java')),str(fixture),str(source)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertIn('PASS:',subprocess.check_output(['java','-cp',tmp,'SignatureFusionGeometryTest'],text=True))
   self.assertIn('20000',subprocess.check_output(['java','-cp',tmp,'FusionReuse'],text=True))

 def test_document_adapter_double_retains_every_native_primitive_argument(self):
  import re
  native=(ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/SendMessagesHelper.java').read_text()
  signatures=re.findall(r'public static void prepareSendingDocuments\(([^\n]+)\)',native)
  actual=next(x for x in signatures if len(x.split(','))==23 and 'SendMessageChatArguments sendMessageChatArguments' in x)
  fixture=(ROOT/'tools/connected_alpha/files_native/stubs.py').read_text()
  double=re.search(r'public static void prepareSendingDocuments\(([^)]+)\)',fixture).group(1)
  primitives=lambda sig:{i:part.strip().split()[0]for i,part in enumerate(sig.split(','))if part.strip().split()[0]in {'long','int','boolean','float','double'}}
  self.assertEqual(primitives(actual),primitives(double))
  self.assertEqual(primitives(actual)[21],'long')
