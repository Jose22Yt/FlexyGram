"""Minimal offline doubles, not a replacement for an Android/Gradle build."""
from pathlib import Path
import shutil


def method(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def write_sources(root, java, main):
    sources = {
'android/content/Context.java': '''package android.content; public class Context { public static final int MODE_PRIVATE=0; public SharedPreferences getSharedPreferences(String n,int m){return org.telegram.messenger.ApplicationLoader.prefs.computeIfAbsent(n,k->new SharedPreferences());}}''',
'android/content/SharedPreferences.java': '''package android.content; import java.util.*; public class SharedPreferences { public Map<String,Object> data=new HashMap<>(); public int getInt(String k,int d){return (int)data.getOrDefault(k,d);} public String getString(String k,String d){return (String)data.getOrDefault(k,d);} public Editor edit(){return new Editor();} public class Editor {public Editor clear(){data.clear();return this;} public Editor putInt(String k,int v){data.put(k,v);return this;} public Editor putString(String k,String v){data.put(k,v);return this;} public void apply(){}}}''',
'android/app/Activity.java': 'package android.app; public class Activity {}',
'android/os/SystemClock.java': 'package android.os; public class SystemClock {public static long elapsedRealtime(){return 1;}}',
'android/text/TextUtils.java': 'package android.text; public class TextUtils {public static boolean isEmpty(String s){return s==null||s.isEmpty();}}',
'android/util/Log.java': '''package android.util; public class Log {public static final int ERROR=6,DEBUG=3; public static int e(String t,String s){org.telegram.messenger.FileLog.e(s);return 0;} public static int d(String t,String s){org.telegram.messenger.FileLog.d(s);return 0;} public static int println(int p,String t,String s){org.telegram.messenger.FileLog.d(s);return 0;}}''',
'androidx/annotation/NonNull.java': 'package androidx.annotation; public @interface NonNull {}',
'com/google/firebase/messaging/FirebaseMessagingService.java': '''package com.google.firebase.messaging; public class FirebaseMessagingService {public void onMessageReceived(RemoteMessage m){} public void onNewToken(String t){}}''',
'com/google/firebase/messaging/RemoteMessage.java': '''package com.google.firebase.messaging; import java.util.*; public class RemoteMessage {public static String token; public String getFrom(){return token;} public Map<String,String> getData(){return Map.of("p",token);} public long getSentTime(){return 7;}}''',
'com/google/firebase/messaging/FirebaseMessaging.java': '''package com.google.firebase.messaging; public class FirebaseMessaging {public static String token; public static Exception error; public static FirebaseMessaging getInstance(){return new FirebaseMessaging();} public Task getToken(){return new Task();} public interface Listener {void onComplete(Task t);} public static class Task {public Task addOnCompleteListener(Listener l){l.onComplete(this);return this;} public boolean isSuccessful(){return error==null;} public Exception getException(){return error;} public String getResult(){return token;}}}''',
'com/google/firebase/FirebaseApp.java': 'package com.google.firebase; public class FirebaseApp {public static void initializeApp(Object c){}}',
'com/google/android/gms/common/ConnectionResult.java': 'package com.google.android.gms.common; public class ConnectionResult {public static final int SUCCESS=0;}',
'com/google/android/gms/common/GoogleApiAvailability.java': '''package com.google.android.gms.common; public class GoogleApiAvailability {public static GoogleApiAvailability getInstance(){return new GoogleApiAvailability();} public int isGooglePlayServicesAvailable(Object c){return 0;}}''',
'xyz/nextalone/nagram/NaConfig.java': '''package xyz.nextalone.nagram; import android.content.SharedPreferences; public class NaConfig {public static NaConfig INSTANCE=new NaConfig(); public static SharedPreferences prefs=new SharedPreferences(); public static SharedPreferences getPreferences(){return prefs;} public NaConfig getPushServiceType(){return this;} public String getKey(){return "push";}}''',
'org/telegram/ui/LaunchActivity.java': 'package org.telegram.ui; public class LaunchActivity {}',
'org/telegram/tgnet/SerializedData.java': '''package org.telegram.tgnet; public class SerializedData {public byte[] data; public static boolean fail; public SerializedData(byte[] b){if(fail)throw new IllegalArgumentException(org.telegram.messenger.P01Harness.SECRET);data=b;} public SerializedData(int n){} public int readInt32(boolean b){return 0;} public byte[] toByteArray(){return data;}}''',
'org/telegram/tgnet/TLObject.java': 'package org.telegram.tgnet; public class TLObject {public String phone_code,password,token; public String toString(){throw new AssertionError("must not stringify protocol body");}}',
'org/telegram/tgnet/TLRPC.java': '''package org.telegram.tgnet; public class TLRPC {public static class TL_auth_loggedOut {public static TL_auth_loggedOut TLdeserialize(SerializedData d,int n,boolean e){return new TL_auth_loggedOut();} public int getObjectSize(){return 0;} public void serializeToStream(SerializedData d){d.data=new byte[0];}} public static class auth_Authorization {public static auth_Authorization TLdeserialize(SerializedData d,int n,boolean e){TL_auth_authorization a=new TL_auth_authorization();a.future_auth_token=d.data;return a;}} public static class TL_auth_authorization extends auth_Authorization {public byte[] future_auth_token; public int getObjectSize(){return future_auth_token.length;} public void serializeToStream(SerializedData d){d.data=future_auth_token;}} public static class TL_error extends TLObject {public int code; public String text;}}''',
'org/telegram/tgnet/ConnectionsManager.java': '''package org.telegram.tgnet; public class ConnectionsManager {public static String result;public static int[] requests; public static ConnectionsManager getInstance(int a){return new ConnectionsManager();} public void native_receivedCaptchaResult(int a,int[] r,String t){requests=r;result=t;}}''',
'org/telegram/messenger/BuildVars.java': 'package org.telegram.messenger; public class BuildVars {public static boolean DEBUG_VERSION,LOGS_ENABLED,DEBUG_PRIVATE_VERSION;}',
'org/telegram/messenger/ApplicationLoader.java': '''package org.telegram.messenger; import java.util.*;import android.content.*; public class ApplicationLoader {public static Map<String,SharedPreferences> prefs=new HashMap<>(); public static Context applicationContext=new Context(); public static int init,starts; public static void postInitApplication(){init++;} public static void startPushService(){starts++;}}''',
'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger; public class AndroidUtilities {public static void runOnUIThread(Runnable r){r.run();} public static android.app.Activity getActivity(){return null;}}''',
'org/telegram/messenger/Utilities.java': '''package org.telegram.messenger; import java.util.HexFormat; public class Utilities {public static Queue globalQueue=new Queue();public static class Queue {public void postRunnable(Runnable r){r.run();}} public static byte[] hexToBytes(String s){return HexFormat.of().parseHex(s);} public static String bytesToHex(byte[] b){return HexFormat.of().formatHex(b);}}''',
'org/telegram/messenger/BackupAgent.java': 'package org.telegram.messenger; public class BackupAgent {public static int calls; public static void requestBackup(){calls++;}}',
'org/telegram/messenger/SharedConfig.java': '''package org.telegram.messenger; public class SharedConfig {public static String pushString,pushStringStatus;public static long pushStringGetTimeStart,pushStringGetTimeEnd;}''',
'org/telegram/messenger/PushListenerController.java': '''package org.telegram.messenger; public class PushListenerController {public static final int PUSH_TYPE_FIREBASE=2;public static String registered,received;public static int sends; public interface IPushListenerServiceProvider {String getLogTitle();int getPushType();void onRequestPushToken();boolean hasServices();} public static void processRemoteMessage(int t,String d,long time){received=d;if(time!=7)throw new AssertionError();} public static void sendRegistrationToServer(int t,String token){registered=token;sends++;}}''',
    }
    sources['ParseSources.java'] = r"""import javax.tools.*;import com.sun.source.util.JavacTask;import java.util.*;
public class ParseSources {public static void main(String[] args)throws Exception {
JavaCompiler compiler=ToolProvider.getSystemJavaCompiler();DiagnosticCollector<JavaFileObject> diagnostics=new DiagnosticCollector<>();
try(StandardJavaFileManager manager=compiler.getStandardFileManager(diagnostics,null,null)) {
JavacTask task=(JavacTask)compiler.getTask(null,manager,diagnostics,List.of("-proc:none"),null,manager.getJavaFileObjects(args));
for(var unit:task.parse()){}
if(diagnostics.getDiagnostics().stream().anyMatch(d->d.getKind()==Diagnostic.Kind.ERROR))throw new AssertionError(diagnostics.getDiagnostics().toString());
}
System.out.println("Java production syntax PASS");}}
"""
    sources['org/telegram/messenger/DiagnosticPolicy.java'] = 'package org.telegram.messenger; public class DiagnosticPolicy {public static boolean isolated=false; public static boolean isIsolated(){return isolated;}}'
    filelog = (java / 'FileLog.java').read_text()
    # Compile and execute these production diagnostic methods verbatim, with
    # synchronous queues/writers so both sink outputs can be asserted offline.
    methods = '\n'.join(method(filelog, signature) for signature in (
        'private static void postProtocolDump', 'public static void dumpResponseAndRequest',
        'public static void dumpUnparsedMessage'))
    sources['org/telegram/messenger/FileLog.java'] = '''package org.telegram.messenger;
import java.io.*;import java.util.*;import java.util.concurrent.atomic.AtomicInteger;
import org.telegram.tgnet.*;import android.util.Log;
public class FileLog {
public static List<String> lines=new ArrayList<>();public static void d(String s){lines.add(s);}public static void e(String s){lines.add(s);}public static void e(Throwable t){lines.add(t.toString());}
static final String tag="test",mtproto_tag="protocol";static final int MAX_PENDING_PROTOCOL_DUMPS=8;static final AtomicInteger pendingProtocolDumps=new AtomicInteger();
static FileLog instance=new FileLog();public static FileLog getInstance(){return instance;}
java.text.SimpleDateFormat dateFormat=new java.text.SimpleDateFormat("yyyy-MM-dd");
Utilities.Queue logQueue=new Utilities.Queue();java.io.Writer tlStreamWriter=new StringWriter();
''' + methods + '\n}'
    push = (java / 'PushListenerController.java').read_text()
    log_calls = '\n'.join(line.strip() for line in push.splitlines() if 'FileLog.' in line and
                          ('DECRYPT ERROR' in line or 'processing failed' in line))
    sources['org/telegram/messenger/P01Harness.java'] = r'''package org.telegram.messenger;
import java.nio.charset.StandardCharsets;import java.util.*;import java.lang.reflect.*;
import org.telegram.tgnet.*;import com.google.firebase.messaging.*;
public class P01Harness {
public static final String SECRET="SYNTHETIC_SECRET_P01_NOT_REAL_937614";
static void check(boolean v){if(!v)throw new AssertionError("functional assertion failed");}
static void safe(){String output=String.join("\n",FileLog.lines)+FileLog.instance.tlStreamWriter.toString();check(!output.contains(SECRET));check(!output.contains(Utilities.bytesToHex(SECRET.getBytes(StandardCharsets.UTF_8))));}
public static void main(String[] args)throws Exception {
for(int flags=0;flags<8;flags++){
BuildVars.DEBUG_VERSION=(flags&1)!=0;BuildVars.LOGS_ENABLED=(flags&2)!=0;BuildVars.DEBUG_PRIVATE_VERSION=(flags&4)!=0;
FileLog.lines.clear();FileLog.instance.tlStreamWriter=new java.io.StringWriter();
AuthTokensHelper.clearLogInTokens();TLRPC.TL_auth_authorization token=new TLRPC.TL_auth_authorization();token.future_auth_token=SECRET.getBytes(StandardCharsets.UTF_8);
int backups=BackupAgent.calls;AuthTokensHelper.saveLogInToken(token);check(BackupAgent.calls==backups+1);check(Arrays.equals(AuthTokensHelper.getSavedLogInTokens().get(0).future_auth_token,token.future_auth_token));
SerializedData.fail=true;check(AuthTokensHelper.getSavedLogInTokens().isEmpty());SerializedData.fail=false;
GcmPushListenerService service=new GcmPushListenerService();service.onNewToken(SECRET);check(SECRET.equals(PushListenerController.registered));RemoteMessage.token=SECRET;service.onMessageReceived(new RemoteMessage());check(SECRET.equals(PushListenerController.received));
int sends=PushListenerController.sends;xyz.nextalone.nagram.NaConfig.prefs.edit().putInt("push",2).apply();service.onNewToken(SECRET);check(PushListenerController.sends==sends);xyz.nextalone.nagram.NaConfig.prefs.edit().putInt("push",1).apply();
SharedConfig.pushString=SECRET;FirebaseMessaging.token=SECRET;FirebaseMessaging.error=null;GooglePushListenerServiceProvider provider=new GooglePushListenerServiceProvider();provider.onRequestPushToken();check(SECRET.equals(PushListenerController.registered));
FirebaseMessaging.error=new IllegalStateException(SECRET,new Exception(SECRET));provider.onRequestPushToken();check(PushListenerController.registered==null);check("IllegalStateException".equals(GooglePushListenerServiceProvider.lastError));check("__FIREBASE_FAILED__".equals(SharedConfig.pushStringStatus));check(provider.hasServices());FirebaseMessaging.error=null;
CaptchaController.request(0,123,"login",SECRET);check("RECAPTCHA_FAILED_NO_ACTIVITY".equals(ConnectionsManager.result));check(ConnectionsManager.requests[0]==123);
Method format=CaptchaController.class.getDeclaredMethod("formatException",Exception.class);format.setAccessible(true);check("IllegalStateException".equals(format.invoke(null,new IllegalStateException(SECRET))));
CaptchaController.Request request=new CaptchaController.Request(0,"login",SECRET);request.requestTokens.add(456);CaptchaController.currentRequests.put(request.hashCode(),request);request.done(SECRET);check(SECRET.equals(ConnectionsManager.result));check(ConnectionsManager.requests[0]==456);
String tag="FCM";Throwable e=new IllegalArgumentException(SECRET,new Exception(SECRET));
''' + log_calls + r'''
TLObject body=new TLObject();body.phone_code=SECRET;body.password=SECRET;body.token=SECRET;TLRPC.TL_error error=new TLRPC.TL_error();error.code=400;error.text=SECRET;
FileLog.dumpResponseAndRequest(0,body,body,null,1,0,2);FileLog.dumpResponseAndRequest(0,body,null,error,1,0,2);FileLog.dumpUnparsedMessage(body,1,0);safe();
if(BuildVars.DEBUG_PRIVATE_VERSION&&BuildVars.LOGS_ENABLED){check(FileLog.lines.stream().anyMatch(s->s.contains("code=400")));}
}
System.out.println("P0.1 Java harness PASS");
}}
'''
    for name, text in sources.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    for name in ('AuthTokensHelper', 'GcmPushListenerService', 'CaptchaController', 'GooglePushListenerServiceProvider'):
        shutil.copyfile(java / (name + '.java'), root / 'org/telegram/messenger' / (name + '.java'))
