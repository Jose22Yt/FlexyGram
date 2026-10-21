"""Verbatim source entry contracts and unapplied integration patches. No Android process."""
from pathlib import Path
import hashlib
import importlib.util
import os
import re
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
BASE='36e27309bee4e6c27e3850321fa0c6c44e2acf42'
MODULE=ROOT/'TMessagesProj_Modules/telegram-session-core/src/main/java'
JAVA='io/github/jose22yt/flexygram/session'

def block(source,signature):
    start=source.index(signature);opening=source.index('{',start)
    depth=0;quote=None;escaped=False
    for pos in range(opening,len(source)):
        char=source[pos]
        if quote:
            if escaped:escaped=False
            elif char=='\\':escaped=True
            elif char==quote:quote=None
        elif char in ['"',"'"]:quote=char
        elif char=='{':depth+=1
        elif char=='}':
            depth-=1
            if depth==0:return source[start:pos+1]
    raise ValueError('UNBALANCED_SOURCE')

def active_source(source):
    # Mask comments while preserving offsets/line numbers and string/char literals.
    out=list(source);i=0;quote=None;escaped=False
    while i<len(source):
        c=source[i]
        if quote:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c==quote:quote=None
        elif c in ['"',"'"]:quote=c
        elif source.startswith('//',i):
            end=source.find('\n',i);end=len(source) if end<0 else end
            for j in range(i,end):out[j]=' '
            i=end-1
        elif source.startswith('/*',i):
            end=source.find('*/',i+2)
            if end<0:raise ValueError('UNTERMINATED_COMMENT')
            for j in range(i,end+2):
                if out[j]!='\n':out[j]=' '
            i=end+1
        i+=1
    return ''.join(out)

def execute_java(folder,files,main):
    java=Path(os.environ['JAVA_HOME'])/'bin'
    compiled=subprocess.run([str(java/'javac'),'--release','8','-d',str(folder/'classes'),*map(str,files)],capture_output=True,text=True)
    if compiled.returncode:raise AssertionError(compiled.stderr)
    result=subprocess.run([str(java/'java'),'-cp',str(folder/'classes'),main],capture_output=True,text=True,timeout=20)
    if result.returncode:raise AssertionError(result.stdout+result.stderr)
    return result.stdout

class IntegrationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name)
        cls.paths=['TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java','TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java','TMessagesProj/src/main/java/tw/nekomimi/nekogram/NekoXConfig.java','TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java','TMessagesProj/jni/tgnet/ConnectionsManager.cpp']
        for path in cls.paths:
            p=cls.folder/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/path).read_bytes())
        for patch in sorted((ROOT/'patches/session-core').glob('*.patch')):
            subprocess.run(['git','apply','--check',str(patch)],cwd=cls.folder,check=True,capture_output=True)
            subprocess.run(['git','apply',str(patch)],cwd=cls.folder,check=True,capture_output=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_no_existing_shared_or_build_files_modified(self):
        changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
        allowed=['TMessagesProj_Modules/telegram-session-core/','tests/session_core/','patches/session-core/','docs/session-core/']
        # Child-stage inventory only: original shared/build files must still be byte-identical.
        allowed+=['TMessagesProj_Modules/telegram-session-android/','tests/session_android/','docs/session-android/']
        for path in changed:self.assertTrue(any(path.startswith(prefix) for prefix in allowed),path)
        for path in self.paths:
            before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
            self.assertEqual((ROOT/path).read_bytes(),before)
        self.assertNotIn('telegram-session-core',(ROOT/'settings.gradle').read_text())
        self.assertNotIn('telegram-session-android',(ROOT/'settings.gradle').read_text())

    def test_scope_matches_fixed_userconfig_and_variant_identities(self):
        source=(ROOT/self.paths[0]).read_text()
        self.assertRegex(source,r'MAX_ACCOUNT_COUNT\s*=\s*10\s*;')
        module=(MODULE/JAVA/'SessionScope.java').read_text()
        import json
        for path,key in [('gradle/real-alpha.json',None),('gradle/beta-development.json',None),('gradle/variant-policy.json','diagnostic')]:
            row=json.loads((ROOT/path).read_text());row=row['variants'][key] if key else row
            self.assertIn('"'+row['applicationId']+'"',module)

    def test_no_network_logging_or_android_backend_in_new_module(self):
        source='\n'.join(p.read_text() for p in MODULE.rglob('*.java'))
        self.assertNotRegex(source,r'import\s+(?:android\.|org\.telegram\.|java\.net\.|okhttp|org\.apache\.http)')
        self.assertNotRegex(source,r'System\.(?:out|err)|printStackTrace\s*\(|FileLog\.|getMessage\s*\(|getCause\s*\(')
        self.assertNotRegex(source,r'\bnative\s+(?:void|boolean|int|long|String)\s+')

    def test_original_null_user_partial_mutation_and_unapplied_fix(self):
        original=(ROOT/self.paths[0]).read_text();patched=(self.folder/self.paths[0]).read_text()
        signature='public void setCurrentUser(TLRPC.User user)'
        sources=[]
        for name,source in [('OriginalUser',original),('PatchedUser',patched)]:
            path=self.folder/(name+'.java')
            path.write_text('class '+name+'{ Object sync=new Object();TLRPC.User currentUser;long clientUserId;int checks;void checkPremiumSelf(TLRPC.User a,TLRPC.User b){checks++;}\n'+block(source,signature)+'\n}')
            sources.append(path)
        main=self.folder/'NullContract.java'
        main.write_text('''class TLRPC{static class User{long id;User(long id){this.id=id;}}}
public class NullContract{static void need(boolean b){if(!b)throw new AssertionError();}public static void main(String[] a){
TLRPC.User first=new TLRPC.User(1),second=new TLRPC.User(2);OriginalUser old=new OriginalUser();old.setCurrentUser(first);
boolean npe=false;try{old.setCurrentUser(null);}catch(NullPointerException e){npe=true;}need(npe&&old.currentUser==null&&old.clientUserId==1);
PatchedUser fixed=new PatchedUser();fixed.setCurrentUser(first);boolean denied=false;try{fixed.setCurrentUser(null);}catch(IllegalArgumentException e){denied=true;}need(denied&&fixed.currentUser==first&&fixed.clientUserId==1&&fixed.checks==1);fixed.setCurrentUser(second);need(fixed.currentUser==second&&fixed.clientUserId==2&&fixed.checks==2);System.out.println("NULL_CONTRACT_REPRODUCED_AND_PATCH_VERIFIED_HOST_ONLY");}}''')
        self.assertIn('PATCH_VERIFIED_HOST_ONLY',execute_java(self.folder,sources+[main],'NullContract'))

    def test_original_debug_reset_and_unapplied_no_reset_patch(self):
        original=(ROOT/self.paths[1]).read_text();patched=(self.folder/self.paths[1]).read_text()
        signature='if (BuildVars.DEBUG_PRIVATE_VERSION && !getUserConfig().isClientActivated() && error != null && error.code == 400 && Objects.equals(error.text, "CONNECTION_NOT_INITED"))'
        old=block(original,signature);self.assertNotIn(signature,patched)
        self.assertRegex((ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java').read_text(),r'DEBUG_PRIVATE_VERSION\s*=\s*false')
        main=self.folder/'ResetContract.java'
        main.write_text('''import java.util.Objects;class BuildVars{static boolean DEBUG_PRIVATE_VERSION=true,LOGS_ENABLED=false;}class FileLog{static void d(String s){}}class Error{int code=400;String text="CONNECTION_NOT_INITED";}
class OldReset{int resets,resends,delivered,currentAccount;Object normalizedObject,onComplete,onCompleteTimestamp,onQuickAck,onWriteToSocket;int flags,datacenterId,connectionType;boolean immediate;OldReset getUserConfig(){return this;}boolean isClientActivated(){return false;}void cleanup(boolean keys){if(keys)resets++;}void sendRequest(Object...args){resends++;}void run(Error error){'''+old+'''delivered++;}}
class PatchedReset{int resets,resends,delivered;void run(Error error){delivered++;}}
public class ResetContract{public static void main(String[] args){OldReset old=new OldReset();old.run(new Error());if(old.resets!=1||old.resends!=1||old.delivered!=0)throw new AssertionError();PatchedReset fixed=new PatchedReset();fixed.run(new Error());if(fixed.resets!=0||fixed.resends!=0||fixed.delivered!=1)throw new AssertionError();System.out.println("IMPLICIT_KEY_RESET_SOURCE_PATH_REPRODUCED_HOST_ONLY");}}''')
        self.assertIn('REPRODUCED_HOST_ONLY',execute_java(self.folder,[main],'ResetContract'))

    def test_unapplied_api_patch_keeps_closed_mode_and_rejects_legacy_overrides(self):
        source=(self.folder/self.paths[2]).read_text()
        methods='\n'.join(block(source,s) for s in ['public static int currentAppId()','public static String currentAppHash()','private static boolean realAlphaProjectApi()'])
        path=self.folder/'ApiContract.java'
        path.write_text('''class BuildConfig{static String FLEXYGRAM_VARIANT="realAlpha",APP_HASH="0123456789abcdef0123456789abcdef";static int APP_ID=123456;}class DiagnosticPolicy{static boolean isolated=true;static boolean isIsolated(){return isolated;}}
public class ApiContract{static int API_TYPE_CUSTOM=1,customApi=1,customAppId=999;static String customAppHash="SYNTHETIC_LEGACY_NOT_PROJECT";'''+methods.replace('org.telegram.messenger.DiagnosticPolicy','DiagnosticPolicy')+'''
static void need(boolean b){if(!b)throw new AssertionError();}public static void main(String[] args){need(currentAppId()==0&&currentAppHash().isEmpty());DiagnosticPolicy.isolated=false;need(currentAppId()==123456&&currentAppHash().equals(BuildConfig.APP_HASH));BuildConfig.APP_ID=6;boolean rejected=false;try{currentAppId();}catch(IllegalStateException e){rejected=true;need(!e.toString().contains(customAppHash));}need(rejected);BuildConfig.APP_ID=123456;BuildConfig.APP_HASH=null;rejected=false;try{currentAppHash();}catch(IllegalStateException e){rejected=true;}need(rejected);BuildConfig.FLEXYGRAM_VARIANT="betaDevelopment";need(currentAppId()==999&&currentAppHash().equals(customAppHash));DiagnosticPolicy.isolated=true;need(currentAppId()==0&&currentAppHash().isEmpty());System.out.println("PRIVATE_PAIR_SELECTION_PATCH_VERIFIED_HOST_ONLY");}}''')
        self.assertIn('PATCH_VERIFIED_HOST_ONLY',execute_java(self.folder,[path],'ApiContract'))

    def test_original_java_login_sinks_and_unapplied_redaction(self):
        original=(ROOT/self.paths[3]).read_text();patched=(self.folder/self.paths[3]).read_text()
        def statement(source,prefix):return next(line.strip() for line in source.splitlines() if prefix in line)
        self.assertIn('FileLog.d("login token to check ',active_source(original))
        self.assertIn('FileLog.d("LoginBilling found ',active_source(original))
        raw_token=statement(original,'FileLog.d("login token to check ')
        raw_billing=statement(original,'FileLog.d("LoginBilling found ')
        safe_token=statement(patched,'FileLog.d("login token candidate available')
        safe_billing=statement(patched,'FileLog.d("LoginBilling product metadata received')
        path=self.folder/'LogContract.java'
        path.write_text('''import java.util.*;import java.nio.charset.StandardCharsets;
class FileLog{static String last;static void d(String text){last=text;}}
class Token{byte[] future_auth_token="SYNTHETIC_PRIVATE_CANARY".getBytes(StandardCharsets.UTF_8);}class Purpose{String currency="SYN";long amount=0;}
public class LogContract{public static void main(String[] args){List<Token> loginTokens=Arrays.asList(new Token());int i=0;String product="SYNTHETIC_PRODUCT",phone="SYNTHETIC_PRIVATE_CANARY",phoneHash="SYNTHETIC_PRIVATE_CANARY";Purpose purpose=new Purpose();'''+raw_token+'''if(!FileLog.last.contains("SYNTHETIC_PRIVATE_CANARY"))throw new AssertionError();'''+safe_token+'''if(FileLog.last.contains("SYNTHETIC_PRIVATE_CANARY"))throw new AssertionError();'''+raw_billing+'''if(!FileLog.last.contains("SYNTHETIC_PRIVATE_CANARY"))throw new AssertionError();'''+safe_billing+'''if(FileLog.last.contains("SYNTHETIC_PRIVATE_CANARY"))throw new AssertionError();System.out.println("SYNTHETIC_JAVA_SINKS_REPRODUCED_PATCH_REDACTED");}}''')
        self.assertIn('PATCH_REDACTED',execute_java(self.folder,[path],'LogContract'))

    def test_original_native_integrity_sink_and_unapplied_redaction(self):
        original=(ROOT/self.paths[4]).read_text();patched=(self.folder/self.paths[4]).read_text()
        self.assertIn('received integrity token, wrapping %s',active_source(original))
        raw=next(line.strip() for line in original.splitlines() if 'received integrity token, wrapping %s' in line)
        safe=next(line.strip() for line in patched.splitlines() if 'received integrity result"' in line)
        source=self.folder/'integrity_log.cpp';binary=self.folder/'integrity_log'
        source.write_text('#include <cstdio>\n#include <cstring>\n#include <string>\nchar sink[1024];\n#define DEBUG_D(...) std::snprintf(sink,sizeof(sink),__VA_ARGS__)\nint main(){bool LOGS_ENABLED=true;int instanceNum=0;std::string token="SYNTHETIC_PRIVATE_CANARY";'+raw+'if(!std::strstr(sink,token.c_str()))return 1;'+safe+'if(std::strstr(sink,token.c_str()))return 2;return 0;}')
        subprocess.run(['c++','-std=c++17',str(source),'-o',str(binary)],check=True,capture_output=True,text=True)
        self.assertEqual(subprocess.run([str(binary)]).returncode,0)

    def test_existing_private_api_pair_resolver_with_synthetic_values(self):
        # Reuse the existing exact resolver regression; do not implement another credential resolver.
        path=ROOT/'tests/security/test_p02_isolation.py'
        spec=importlib.util.spec_from_file_location('existing_pair_contract',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            parent=Path(d)/'wrapper/dists/gradle-9.7.1-bin/local';parent.mkdir(parents=True)
            (parent/'gradle-9.7.1').symlink_to(Path(os.environ['FLEXYGRAM_GRADLE_HOME']))
            with patch.dict(os.environ,{'GRADLE_USER_HOME':d}):
                module.IsolationTests.test_actual_pair_resolver_complete_precedence_and_invalid_inputs(self)
