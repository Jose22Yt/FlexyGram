"""Execute real failure mapping without exposing hostile or private exception values."""
from pathlib import Path
import tempfile,subprocess,unittest
class Errors(unittest.TestCase):
 def test_stage_messages_and_secret_redaction(self):
  s=(Path(__file__).parent/'android/src/io/github/jose22yt/flexygram/delivery/MainActivity.java').read_text();a=s.index('    static String failureMessage(');b=s.index('    private void startInstall()',a);method=s[a:b]
  code='public class SafeErrors {'+method+'''static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){check(failureMessage(0,new Exception()).contains("espacio"));check(failureMessage(1,new Exception()).contains("FlexyGram-Alpha1271-ARM64.tar.age"));check(failureMessage(2,new Exception()).contains("flexygram-delivery.agekey"));check(failureMessage(3,new Exception("installed version rejected")).contains("bajar de versión"));check(failureMessage(3,new Exception("installed certificate rejected")).contains("firma"));for(int i=0;i<5;i++)check(!failureMessage(i,new Exception("SECRET_SENTINEL")).contains("SECRET_SENTINEL"));}}'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'SafeErrors.java';p.write_text(code);subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(p)],check=True);subprocess.run(['java','-cp',d,'SafeErrors'],check=True)
