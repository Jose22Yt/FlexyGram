from pathlib import Path
import importlib.util,sys,subprocess
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/native_login_wiring'))
import fixtures as previous
sys.path.insert(0,str(ROOT/'tools/native_login_pages'))
from prepare_patch import span

def write(folder,temporary):
    metadata=previous.write(folder)
    root=temporary/'patched'
    for name in ['TMessagesProj/build.gradle','TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java']:
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    for directory in ['patches/native-login-wiring','patches/native-login-pages']:
        for patch in sorted((ROOT/directory).glob('*.patch')):
            if directory=='patches/native-login-wiring' and patch.name.startswith('0001'):continue
            subprocess.run(['git','apply','--check',str(patch)],cwd=root,check=True,capture_output=True)
            subprocess.run(['git','apply',str(patch)],cwd=root,check=True,capture_output=True)
    patched=(root/'TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java').read_text()
    def first_guard(classname,method):
        a,b,c=span(patched,'public class '+classname);body=patched[a:c]
        x,y,z=span(body,method);tail=body[y+1:z].lstrip()
        if not tail.startswith('if (localLoginClosed())'):raise RuntimeError('MISSING_FIRST_GUARD:'+classname+method)
        if '{' in tail[:tail.index(';')]:_,_,end=span(tail,'if (localLoginClosed())');return tail[:end]
        return tail[:tail.index(';')+1]
    source='''package io.github.jose22yt.flexygram.login;import android.os.Bundle;import io.github.jose22yt.flexygram.login.local.*;
public class OriginalGuardHost {
boolean isolated=true;int legacy,apply;int currentViewNum=2;LocalLoginSession preparedLocalSession;EphemeralPages.View preparedLocalView;
public OriginalGuardHost(LocalLoginSession session,EphemeralPages.View view){preparedLocalSession=session;preparedLocalView=view;}
boolean localLoginClosed(){return isolated;}boolean localViewActive(){return preparedLocalSession.valid(preparedLocalView,0);}void clearClosedLocalInputs(){}void localClearPage(int n){}void localApplyPage(int n){apply++;}void localCancelPages(){preparedLocalSession.cancel(preparedLocalView);}
void localPhoneNext(CharSequence a,CharSequence b){char[] c=NativeUiInput.copy(a,b);try{preparedLocalSession.phone(preparedLocalView,c);}finally{NativeUiInput.wipe(c);}}
void localCodeNext(CharSequence a){char[] c=NativeUiInput.copy(a);try{preparedLocalSession.code(preparedLocalView,c);}finally{NativeUiInput.wipe(c);}}
void localPasswordNext(CharSequence a){char[] c=NativeUiInput.copy(a);try{preparedLocalSession.password(preparedLocalView,c);}finally{NativeUiInput.wipe(c);}}
void localRegisterNext(CharSequence a,CharSequence b){char[] c=NativeUiInput.copy(a),d=NativeUiInput.copy(b);try{preparedLocalSession.register(preparedLocalView,c,d);}finally{NativeUiInput.wipe(c);NativeUiInput.wipe(d);}}
class Input {String value="000000";CharSequence getText(){return value;}}class Container {String getCode(){return "000000";}}
'''
    signatures={'PhoneView':['public void onNextPressed(String code)'],'LoginActivitySmsView':['public void onNextPressed(String code)','public void setParams(Bundle params, boolean restore)','public boolean onBackPressed(boolean force)','public void onShow()'],'LoginActivityPasswordView':['public void onNextPressed(String code)','public void onShow()'],'LoginActivityRegisterView':['public void onNextPressed(String code)'],'LoginActivityQrView':['public void onShow()','public void exportLoginToken(boolean show)']}
    for name,methods in signatures.items():
        source+='public class '+name+' {Input codeField=new Input(),phoneField=new Input(),firstNameField=new Input(),lastNameField=new Input();Container codeFieldContainer=new Container();\n'
        for signature in methods:
            guard=first_guard(name,signature)
            source+=signature+'{'+guard+'legacy++;'+('return false;' if signature.startswith('public boolean ') else '')+'}\n'
        source+='}\n'
    source+='}\n';(folder/'OriginalGuardHost.java').write_text(source)
    return metadata,patched,root
