"""Host execution of the exact proposed cleanup and original CodeFieldContainer.setText.
Only editor/framework objects are doubles. This is not an Android UI test.
"""
from pathlib import Path
import hashlib, os, subprocess, tempfile, unittest, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/native_login_pages'))
from prepare_patch import span


def method(source, signature):
    a, _, c = span(source, signature)
    return source[a:c]


class OriginalEditorCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.java = Path(os.environ['JAVA_HOME']) / 'bin'
        helper = (ROOT / 'tools/native_login_pages/native_methods.txt').read_text()
        original_path = ROOT / 'TMessagesProj/src/main/java/org/telegram/ui/CodeFieldContainer.java'
        original = original_path.read_text()
        cls.original_hash = hashlib.sha256(original_path.read_bytes()).hexdigest()
        setters = '\n'.join(method(original, s) for s in [
            'public void setText(String code)', 'public void setText(String code, boolean fromPaste)'])
        source = '''
import android.widget.EditText;
public class CleanupHarness {
 static final int VIEW_PHONE_INPUT=0, VIEW_CODE_MESSAGE=1, VIEW_CODE_SMS=2, VIEW_REGISTER=5, VIEW_PASSWORD=6;
 Object[] views=new Object[20];
 static class CodeFieldContainer {
  EditText[] codeField; boolean ignoreOnTextChange;
 SETTERS
 }
 static class PhoneView {EditText codeField=new EditText(),phoneField=new EditText();}
 static class LoginActivitySmsView {CodeFieldContainer codeFieldContainer;Object currentParams,phone,phoneHash,requestPhone,emailPhone;}
 static class LoginActivityPasswordView {EditText codeField=new EditText();Object currentParams,currentPassword,passwordString,requestPhone,phoneHash,phoneCode;}
 static class LoginActivityRegisterView {EditText firstNameField=new EditText(),lastNameField=new EditText();Object currentParams,requestPhone,phoneHash;}
 CLEANUP
 static void require(boolean yes){if(!yes)throw new IllegalStateException("HOST_CLEANUP_CONTRACT_FAILED");}
 public static void main(String[] args){
  CleanupHarness h=new CleanupHarness();LoginActivitySmsView p=new LoginActivitySmsView();h.views[2]=p;
  p.currentParams=p.phone=p.phoneHash=p.requestPhone=p.emailPhone=new Object();
  p.codeFieldContainer=new CodeFieldContainer();CodeFieldContainer c=p.codeFieldContainer;
  c.codeField=new EditText[]{new EditText(),new EditText()};
  for(EditText f:c.codeField){f.value="SYNTHETIC_EDITOR_CANARY";f.notifyEdit=()->{if(!c.ignoreOnTextChange)throw new IllegalStateException("UNEXPECTED_EDITOR_CALLBACK");};}
  switch(args[0]){
   case "clear":h.localClearPage(2);for(EditText f:c.codeField)require(f.value.isEmpty());require(!c.ignoreOnTextChange);break;
   case "suppressed":c.ignoreOnTextChange=true;h.localClearPage(2);for(EditText f:c.codeField)require(f.value.isEmpty());require(c.ignoreOnTextChange);break;
   case "unavailable":p.codeFieldContainer=null;h.localClearPage(2);break;
   case "partial":c.codeField=new EditText[]{c.codeField[0],null};h.localClearPage(2);require(c.codeField[0].value.isEmpty());break;
   case "absentArray":c.codeField=null;h.localClearPage(2);break;
   default:throw new IllegalArgumentException("UNKNOWN_CASE");
  }
  require(p.currentParams==null&&p.phone==null&&p.phoneHash==null&&p.requestPhone==null&&p.emailPhone==null);
  System.out.println("HOST_ORIGINAL_EDITOR_CLEANUP_ONLY");
 }
}
'''.replace(' SETTERS', setters).replace(' CLEANUP', method(helper, 'private void localClearPage(int page)'))
        (cls.root / 'CleanupHarness.java').write_text(source)
        field = cls.root / 'android/widget/EditText.java'
        field.parent.mkdir(parents=True)
        field.write_text('''package android.widget;
public class EditText {public String value="";public Runnable notifyEdit;
public void setText(String s){value=s;if(notifyEdit!=null)notifyEdit.run();}
public boolean isFocused(){return false;}}
''')
        compiled = subprocess.run([str(cls.java / 'javac'), '--release', '8', '-d', str(cls.root),
                                    str(field), str(cls.root / 'CleanupHarness.java')], capture_output=True, text=True)
        if compiled.returncode:raise RuntimeError(compiled.stderr)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def check(self, case):
        result = subprocess.run([str(self.java / 'java'), '-cp', str(self.root), 'CleanupHarness', case],
                                capture_output=True, text=True, timeout=15)
        self.assertNotIn('SYNTHETIC_EDITOR_CANARY', result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('HOST_ORIGINAL_EDITOR_CLEANUP_ONLY', result.stdout)

    def test_original_editor_digits_cleared(self):self.check('clear')
    def test_existing_suppression_restored(self):self.check('suppressed')
    def test_unavailable_container_still_clears_metadata(self):self.check('unavailable')
    def test_partial_editor_array(self):self.check('partial')
    def test_absent_editor_array(self):self.check('absentArray')

if __name__ == '__main__':unittest.main()
