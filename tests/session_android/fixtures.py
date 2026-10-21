"""HOST doubles, never packaged. Real AccountInstance and DiagnosticPolicy are compiled unchanged."""
from pathlib import Path
import hashlib,re
ROOT=Path(__file__).resolve().parents[2]

def write_fixtures(folder):
    def put(path,source):
        p=folder/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
    put('android/content/SharedPreferences.java','package android.content;public interface SharedPreferences {boolean contains(String name);}')
    put('android/content/Context.java','''package android.content;import java.io.File;public class Context {
public String pkg="io.github.jose22yt.flexygram.realalpha";public final File root;public Context(File root){this.root=root;root.mkdirs();}
public Context getApplicationContext(){return this;}public String getPackageName(){return pkg;}
public File getFilesDir(){File f=new File(root,"files");f.mkdirs();return f;}public File getNoBackupFilesDir(){File f=new File(root,"no_backup");f.mkdirs();return f;}}''')
    put('android/os/Looper.java','''package android.os;public class Looper {private static final Looper MAIN=new Looper();public static boolean main;
public static Looper getMainLooper(){return MAIN;}public static Looper myLooper(){return main?MAIN:null;}}''')
    put('android/os/Handler.java','''package android.os;import java.util.*;public class Handler {public static boolean accept=true;public static final List<Runnable> pending=new ArrayList<>();
public Handler(Looper l){}public boolean post(Runnable r){if(accept)pending.add(r);return accept;}public static void flush(){for(Runnable r:new ArrayList<>(pending))r.run();pending.clear();}}''')
    put('android/os/Bundle.java','''package android.os;import java.util.*;public class Bundle {public final Map<String,Object> values=new HashMap<>();
public void putBoolean(String k,boolean v){values.put(k,v);}public void putInt(String k,int v){values.put(k,v);}
public boolean getBoolean(String k,boolean d){return values.containsKey(k)?(Boolean)values.get(k):d;}public int getInt(String k,int d){return values.containsKey(k)?(Integer)values.get(k):d;}}''')
    put('android/os/Process.java','''package android.os;public class Process {public static int deltaPid,deltaUid;
public static int myPid(){return Integer.parseInt(java.lang.management.ManagementFactory.getRuntimeMXBean().getName().split("@")[0])+deltaPid;}
public static int myUid(){return Integer.parseInt(System.getenv("FLEXYGRAM_HOST_UID"))+deltaUid;}}''')
    put('android/util/AtomicFile.java','''package android.util;import java.io.*;
/** HOST rename/sync double, not proof of Android AtomicFile runtime semantics. */
public class AtomicFile {final File base,backup;public AtomicFile(File f){base=f;backup=new File(f+".bak");}
public FileInputStream openRead()throws FileNotFoundException{if(backup.exists()){base.delete();if(!backup.renameTo(base))throw new FileNotFoundException();}return new FileInputStream(base);}
public FileOutputStream startWrite()throws IOException{if(base.exists()&&!base.renameTo(backup))throw new IOException();return new FileOutputStream(base);}
public void finishWrite(FileOutputStream s){try{s.getFD().sync();s.close();if(backup.exists()&&!backup.delete())throw new IOException();}catch(IOException e){throw new IllegalStateException();}}
public void failWrite(FileOutputStream s){try{s.close();}catch(IOException e){}base.delete();backup.renameTo(base);}}''')
    digest=hashlib.sha256((ROOT/'gradle/real-alpha.json').read_bytes()).hexdigest()
    put('org/telegram/messenger/BuildConfig.java','''package org.telegram.messenger;public class BuildConfig {
public static String FLEXYGRAM_VARIANT="realAlpha",FLEXYGRAM_POLICY_SCOPE="'''+digest+''':realAlpha",APP_HASH="";public static int APP_ID=0;
public static boolean ISOLATED_DIAGNOSTIC=true,FLEXYGRAM_CAP_AUTHENTICATION,FLEXYGRAM_CAP_TELEGRAMTRANSPORT,FLEXYGRAM_CAP_PUSH,FLEXYGRAM_CAP_TRANSLATION,FLEXYGRAM_CAP_PLUGINS,FLEXYGRAM_CAP_SESSIONRESTORE;}''')
    put('org/telegram/messenger/DiagnosticPolicy.java',(ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/DiagnosticPolicy.java').read_text())
    put('org/telegram/messenger/ApplicationLoader.java','''package org.telegram.messenger;import android.content.Context;import java.io.File;public class ApplicationLoader {
public static Context applicationContext;public static File overrideFiles;public static File getFilesDirFixed(){return overrideFiles!=null?overrideFiles:applicationContext.getFilesDir();}}''')
    put('org/telegram/messenger/UserConfig.java','''package org.telegram.messenger;import java.util.*;import android.content.SharedPreferences;public class UserConfig {
public static final int MAX_ACCOUNT_COUNT=10;public static int selectedAccount=9;public boolean active;public long id;public final Set<String> keys=new HashSet<>();private static final UserConfig[] instances=new UserConfig[10];
public static UserConfig getInstance(int n){if(instances[n]==null)instances[n]=new UserConfig();return instances[n];}
public boolean isClientActivated(){return active;}public Object getCurrentUser(){return active?this:null;}public long getClientUserId(){return id;}
public SharedPreferences getPreferences(){return (SharedPreferences)java.lang.reflect.Proxy.newProxyInstance(SharedPreferences.class.getClassLoader(),new Class[]{SharedPreferences.class},(proxy,method,args)->{if(method.getName().equals("contains"))return keys.contains((String)args[0]);throw new UnsupportedOperationException("READ_ONLY_FIXTURE");});}}''')
    put('org/telegram/messenger/MessagesStorage.java','''package org.telegram.messenger;public class MessagesStorage {public static boolean fail;
public static MessagesStorage getInstance(int n){if(fail)throw new IllegalStateException("SYNTHETIC_PRIVATE_ADAPTER_401");return new MessagesStorage();}public Object getStorageQueue(){return this;}}''')
    put('org/telegram/tgnet/ConnectionsManager.java','''package org.telegram.tgnet;public class ConnectionsManager {public static int sends,cancels,initializations;
public static ConnectionsManager getInstance(int n){return new ConnectionsManager();}}''')
    source=(ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/AccountInstance.java').read_text()
    put('org/telegram/messenger/AccountInstance.java',source)
    for name in sorted(set(re.findall(r'return (\w+)\.getInstance\(currentAccount\)',source))):
        if name in ('MessagesStorage','ConnectionsManager','UserConfig'):continue
        package='org.telegram.messenger'
        if name=='PersistColorPalette':package='org.telegram.ui.Components.Paint'
        if name in ('CloudStorageHelper','UserHelper','MessageHelper'):package='tw.nekomimi.nekogram.helpers'
        extra='public static android.content.SharedPreferences getNotificationsSettings(int n){return null;}' if name=='MessagesController' else ''
        put(package.replace('.','/')+'/'+name+'.java','package '+package+';public class '+name+' {public static '+name+' getInstance(int n){return new '+name+'();}'+extra+'}')
    source=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/BaseFragment.java').read_text()
    getter=re.search(r'public int getCurrentAccount\(\)\s*\{[^}]+\}',source).group(0)
    put('org/telegram/ui/LoginActivity.java','package org.telegram.ui;public class LoginActivity {private final int currentAccount;public LoginActivity(int n){currentAccount=n;}'+getter+'}')
