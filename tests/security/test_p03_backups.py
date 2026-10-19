"""Offline execution of production backup boundaries with synthetic Android doubles.
Requires JDK and Gson 2.14.0 (GSON_JAR); never starts Android or uses the network.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from java_harness import method

ROOT = Path(__file__).resolve().parents[2]
JAVA = ROOT / 'TMessagesProj/src/main/java'

class BackupTests(unittest.TestCase):
    def test_production_export_import_and_agent(self):
        gson = os.environ.get('GSON_JAR')
        self.assertTrue(gson and Path(gson).is_file(), 'Set GSON_JAR to the cached Gson dependency')
        source = (JAVA/'tw/nekomimi/nekogram/helpers/SettingsBackupHelper.java').read_text()
        methods = '\n'.join(method(source, signature) for signature in [
            'public static String backupSettingsJson(boolean isCloud, int indentSpaces)',
            'public static String backupSettingsJson(boolean isCloud, int indentSpaces, boolean includeApiKeys)',
            'private static void spToJSON(String sp, JSONObject object, Function<String, Boolean> filter)',
            'private static void spToJSON(String sp, JSONObject object, Function<String, Boolean> filter, boolean includeApiKeys)',
            'public static void importSettings(JsonObject configJson)',
            'private static boolean isDeviceSpecificPushKey(String key)'])
        sources = {
            'Helper.java': 'import android.app.Activity; import android.content.*; import org.json.*; import com.google.gson.*; import java.util.*; import java.util.function.Function; import org.telegram.messenger.*; import xyz.nextalone.nagram.NaConfig; import kotlin.text.StringsKt; public class Helper {'+methods+'}',
            'android/content/SharedPreferences.java': '''package android.content; import java.util.*; public class SharedPreferences {public Map<String,Object> data=new HashMap<>(); public Map<String,?> getAll(){return data;} public Editor edit(){return new Editor();} public class Editor {public Editor putBoolean(String k,boolean v){data.put(k,v);return this;} public Editor putInt(String k,int v){data.put(k,v);return this;} public Editor putLong(String k,long v){data.put(k,v);return this;} public Editor putFloat(String k,float v){data.put(k,v);return this;} public Editor putString(String k,String v){data.put(k,v);return this;} public boolean commit(){return true;}}}''',
            'android/content/Context.java': '''package android.content; import java.util.*; public class Context {public Map<String,SharedPreferences> stores=new HashMap<>(); public Set<String> opened=new HashSet<>(); public SharedPreferences getSharedPreferences(String n,int mode){opened.add(n);return stores.computeIfAbsent(n,k->new SharedPreferences());}}''',
            'android/app/Activity.java': 'package android.app; public class Activity {public static final int MODE_PRIVATE=0;}',
            'org/telegram/messenger/ApplicationLoader.java': 'package org.telegram.messenger; public class ApplicationLoader {public static android.content.Context applicationContext=new android.content.Context();}',
            'org/telegram/messenger/PushListenerController.java': 'package org.telegram.messenger; public class PushListenerController {public static void reconcilePushRegistration(){}}',
            'GsonUtil.java': 'import com.google.gson.*; public class GsonUtil {public static JsonObject toJsonObject(String s){return JsonParser.parseString(s).getAsJsonObject();}}',
            'org/json/JSONException.java': 'package org.json; public class JSONException extends Exception {}',
            'org/json/JSONObject.java': '''package org.json; import com.google.gson.*; public class JSONObject {JsonObject data=new JsonObject(); public JSONObject(){} public JSONObject(String s){data=JsonParser.parseString(s).getAsJsonObject();} public void put(String k,Object v){data.add(k,v instanceof JSONObject?((JSONObject)v).data:new Gson().toJsonTree(v));} public String toString(){return data.toString();} public String toString(int spaces){return data.toString();}}''',
            'kotlin/text/StringsKt.java': 'package kotlin.text; public class StringsKt {public static String substringBeforeLast(String s,String delimiter,String fallback){int i=s.lastIndexOf(delimiter);return i<0?fallback:s.substring(0,i);}}',
            'xyz/nextalone/nagram/NaConfig.java': '''package xyz.nextalone.nagram; public class NaConfig {public static final NaConfig INSTANCE=new NaConfig(); public Item getPushServiceTypeUnifiedSimple(){return new Item("PushServiceTypeUnifiedSimple");} public Item getPushServiceTypeUnifiedWebPushPrivateKey(){return new Item("PushServiceTypeUnifiedWebPushPrivateKey");} public Item getPushServiceTypeUnifiedWebPushPublicKey(){return new Item("PushServiceTypeUnifiedWebPushPublicKey");} public Item getPushServiceTypeUnifiedWebPushAuthSecret(){return new Item("PushServiceTypeUnifiedWebPushAuthSecret");} public static class Item {String key; Item(String k){key=k;} public String getKey(){return key;}}}''',
            'org/telegram/messenger/DiagnosticPolicy.java': 'package org.telegram.messenger; public class DiagnosticPolicy {public static boolean isIsolated(){return false;}}',
            'android/os/ParcelFileDescriptor.java': 'package android.os; public class ParcelFileDescriptor {}',
            'android/app/backup/FullBackupDataOutput.java': 'package android.app.backup; public class FullBackupDataOutput {}',
            'android/app/backup/BackupDataInput.java': 'package android.app.backup; public class BackupDataInput {}',
            'android/app/backup/BackupAgentHelper.java': '''package android.app.backup; import android.os.ParcelFileDescriptor; import java.io.*; public class BackupAgentHelper {public static int helpers,restores; public static File target; public void onCreate(){} public void addHelper(String n,Object h){helpers++;} public void onRestore(BackupDataInput d,int v,ParcelFileDescriptor p){restores++;} public void onRestoreFile(ParcelFileDescriptor d,long size,int t,String domain,String path,long mode,long mtime)throws IOException{} public void onFullBackup(FullBackupDataOutput d){} public void onRestoreFile(ParcelFileDescriptor d,long size,File file,int t,long mode,long mtime)throws IOException{target=file;}}''',
            'Main.java': r'''import com.google.gson.*; import android.content.*; import org.telegram.messenger.*; public class Main {
static final String SECRET="SYNTHETIC_SESSION_DO_NOT_EXPORT_P03";
static void ok(boolean b){if(!b)throw new AssertionError();}
static SharedPreferences prefs(String n){return ApplicationLoader.applicationContext.getSharedPreferences(n,0);}
public static void main(String[] args)throws Exception{
// Actual production export: both entrypoints, cloud/local and includeApiKeys true/false.
prefs("saved_tokens").data.put("tokens",SECRET); prefs("saved_tokens_login").data.put("tokens",SECRET);
prefs("userconfing").data.put("passcodeHash",SECRET);
prefs("mainconfig").data.put("fontSize",18); prefs("mainconfig").data.put("autoplayGifs",true);
prefs("mainconfig").data.put("pushString",SECRET); prefs("mainconfig").data.put("directShareHash",SECRET);
prefs("nkmrcfg").data.put("showSeconds",true); prefs("nkmrcfg").data.put("stickerSize",15.5f);
for(String k:new String[]{"LlmApiKey","api_hash","AUTH_KEY","PushServiceTypeUnifiedWebPushAuthSecret","newUnknownCredential"})prefs("nkmrcfg").data.put(k,SECRET);
prefs("aiConfig").data.put("apiKey",SECRET); prefs("themeconfig").data.put("lastDayTheme","Blue");
for(boolean cloud:new boolean[]{false,true})for(boolean include:new boolean[]{false,true}){
String out=Helper.backupSettingsJson(cloud,0,include);ok(!out.contains(SECRET));JsonObject parsed=JsonParser.parseString(out).getAsJsonObject();
ok(parsed.getAsJsonObject("mainconfig").get("fontSize").getAsInt()==18);
ok(parsed.getAsJsonObject("nkmrcfg").get("stickerSize_float").getAsDouble()==15.5);
ok(!Helper.backupSettingsJson(cloud,0).contains(SECRET));}
// Actual import: reject arbitrary preference namespaces BEFORE opening them.
JsonObject attack=JsonParser.parseString("{\"saved_tokens\":{\"tokens\":\"REPLACEMENT\"},\"userconfig2\":{\"user\":\"REPLACEMENT\"},\"../com.exteraless.app/shared_prefs/userconfing\":{\"x\":true},\"mainconfig\":{\"fontSize\":22,\"pushString\":\"REPLACEMENT\"},\"nkmrcfg\":{\"showSeconds\":false,\"stickerSize_float\":16.0,\"LlmApiKey\":\"REPLACEMENT\",\"pluginsDevMode\":true}}").getAsJsonObject();
ApplicationLoader.applicationContext.opened.clear();Helper.importSettings(attack);
ok(ApplicationLoader.applicationContext.opened.equals(java.util.Set.of("mainconfig","nkmrcfg")));
ok(prefs("saved_tokens").data.get("tokens").equals(SECRET));ok(prefs("userconfing").data.get("passcodeHash").equals(SECRET));
ok(prefs("mainconfig").data.get("pushString").equals(SECRET));ok(prefs("mainconfig").data.get("fontSize").equals(22));
ok(prefs("nkmrcfg").data.get("showSeconds").equals(false));ok(prefs("nkmrcfg").data.get("stickerSize").equals(16.0f));
// Malformed sections/types, suffix spoofing, integer overflow, NaN, nested credentials.
for(String bad:new String[]{"{\"mainconfig\":null}","{\"mainconfig\":[]}","{\"mainconfig\":{\"fontSize\":\"22\",\"fontSize_long\":22,\"fontSize\":2147483648}}","{\"nkmrcfg\":{\"showSeconds\":{\"token\":\"x\"},\"stickerSize_float\":1e999}}"}){
JsonObject clean=SettingsBackupPolicy.sanitize(JsonParser.parseString(bad).getAsJsonObject());ok(clean.size()==0);Helper.importSettings(clean);}
JsonObject clean=SettingsBackupPolicy.sanitize(attack);ok(clean.equals(SettingsBackupPolicy.sanitize(clean)));ok(attack.has("saved_tokens"));
BackupAgent agent=new BackupAgent();agent.onCreate();agent.requestBackup();agent.onRestore(null,1,null);agent.onFullBackup(null);agent.onRestoreFile(null,0,new java.io.File("synthetic_saved_tokens.xml"),1,0,0);
ok(android.app.backup.BackupAgentHelper.helpers==0);ok(android.app.backup.BackupAgentHelper.restores==0);ok(android.app.backup.BackupAgentHelper.target==null);
System.out.println("PASS: production export/import, synthetic credentials unchanged, fail-closed policy, legacy restore discarded");
}}
'''}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, body in sources.items():
                target=root/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(body)
            for name in ['SettingsBackupPolicy','BackupAgent']:
                target=root/f'org/telegram/messenger/{name}.java'; target.write_text((JAVA/f'org/telegram/messenger/{name}.java').read_text())
            compile_result=subprocess.run(['javac','-cp',gson,'-d',str(root),*[str(p) for p in root.rglob('*.java')]],capture_output=True,text=True)
            self.assertEqual(compile_result.returncode,0,compile_result.stderr)
            result=subprocess.run(['java','-cp',str(root)+os.pathsep+gson,'Main'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            print(result.stdout.strip())

    def test_no_credential_opt_in_or_automatic_backup_registration(self):
        helper=(JAVA/'tw/nekomimi/nekogram/helpers/CloudSettingsHelper.java').read_text()
        self.assertIn('private final boolean includeApiKeys = false;', helper)
        self.assertNotIn('includeApiKeys = value', helper)
        agent=(JAVA/'org/telegram/messenger/BackupAgent.java').read_text()
        self.assertNotIn('addHelper(',agent)
        self.assertNotIn('dataChanged(',agent)
        manifest=(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').read_text()
        self.assertNotIn('android:backupAgent=',manifest)
        self.assertIn('android:allowBackup="false"',manifest)
