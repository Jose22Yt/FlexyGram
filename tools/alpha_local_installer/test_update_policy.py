"""Execute the production update policy with host package metadata fixtures.

This does not replace Android PackageManager signature verification or a physical
update test. No fixture signer or identity is accepted by the delivery profile.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class UpdatePolicy(unittest.TestCase):
    def test_original_signer_and_non_decreasing_version_are_required(self):
        source = (ROOT/'android/src/io/github/jose22yt/flexygram/delivery/Contract.java').read_text()
        start = source.index('    static void requireCompatibleUpdate(')
        opening = source.index('{', start)
        depth, end = 1, opening + 1
        while depth:
            depth += (source[end] == '{') - (source[end] == '}')
            end += 1
        method = source[start:end]
        runner = '''
import java.io.IOException;
public class UpdatePolicyRegression {
 static class Signature {
  byte[] bytes; Signature(int id) { bytes = new byte[]{(byte)id}; }
  byte[] toByteArray() { return bytes; }
 }
 static class SigningInfo {
  Signature[] signers;
  SigningInfo(Signature... signers) { this.signers = signers; }
  Signature[] getApkContentsSigners() { return signers; }
 }
 static class PackageInfo {
  long version; SigningInfo signingInfo;
  PackageInfo(long version, Signature... signers) {
   this.version=version; signingInfo=new SigningInfo(signers);
  }
  long getLongVersionCode() { return version; }
 }
 _METHOD_
 static void reject(PackageInfo a, PackageInfo b) throws Exception {
  try { requireCompatibleUpdate(a,b); }
  catch(IOException expected) { return; }
  throw new AssertionError("incompatible update accepted");
 }
 public static void main(String[] args) throws Exception {
  Signature original = new Signature(1), other = new Signature(2);
  PackageInfo candidate = new PackageInfo(1267,original);
  requireCompatibleUpdate(new PackageInfo(1261,original),candidate);
  requireCompatibleUpdate(new PackageInfo(1262,original),candidate);
  requireCompatibleUpdate(new PackageInfo(1263,original),candidate);
  requireCompatibleUpdate(new PackageInfo(1264,original),candidate);
  requireCompatibleUpdate(new PackageInfo(1265,original),candidate);
  requireCompatibleUpdate(new PackageInfo(1266,original),candidate);
  requireCompatibleUpdate(new PackageInfo(1267,original),candidate);
  reject(new PackageInfo(1268,original),candidate);
  reject(new PackageInfo(1261,other),candidate);
  reject(new PackageInfo(1261,original,other),candidate);
  reject(new PackageInfo(1261),candidate);
  reject(new PackageInfo(1261,original),new PackageInfo(1262,original,other));
  PackageInfo unsigned = new PackageInfo(1261); unsigned.signingInfo=null;
  reject(unsigned,candidate); reject(candidate,unsigned);
  reject(null,candidate); reject(candidate,null);
  System.out.println("PASS: actual production update policy; host metadata fixtures only");
 }
}'''.replace('_METHOD_',method)
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/'UpdatePolicyRegression.java'
            file.write_text(runner)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(file)],check=True)
            result = subprocess.check_output(['java','-cp',tmp,'UpdatePolicyRegression'],text=True)
            self.assertIn('PASS:', result)
        self.assertIn('requireCompatibleUpdate(c.getPackageManager().getPackageInfo(APP, PackageManager.GET_SIGNING_CERTIFICATES), p)',source)


if __name__ == '__main__':
    unittest.main()
