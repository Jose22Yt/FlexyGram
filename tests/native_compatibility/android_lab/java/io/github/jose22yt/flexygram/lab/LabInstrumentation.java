package io.github.jose22yt.flexygram.lab;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Process;
import android.system.Os;
import android.system.OsConstants;
import java.io.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.json.*;

/** Test APK only. No app imports, network, plugin start or mutable policy overrides. */
public final class LabInstrumentation extends Instrumentation {
    private Bundle args;
    private String stage = "preflight";
    @Override public void onCreate(Bundle arguments) { args=arguments; start(); }
    private static void need(boolean ok,String error) { if (!ok) throw new IllegalStateException(error); }
    private static String read(InputStream input) throws IOException {
        try(InputStream in=input;ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            byte[] b=new byte[8192];int n;
            while((n=in.read(b))!=-1) { out.write(b,0,n);need(out.size()<1048576,"Bounded input exceeded"); }
            return new String(out.toByteArray(),StandardCharsets.UTF_8);
        }
    }
    private String asset(String name) throws IOException {return read(getContext().getAssets().open(name));}
    private static String hex(byte[] bytes) {
        StringBuilder b=new StringBuilder();for(byte v:bytes)b.append(String.format(java.util.Locale.ROOT,"%02x",v&255));return b.toString();
    }
    private static String sha(File file) throws Exception {
        MessageDigest h=MessageDigest.getInstance("SHA-256");
        try(InputStream in=new FileInputStream(file)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)h.update(b,0,n);}
        return hex(h.digest());
    }
    private static String property(String name) throws Exception {
        java.lang.Process p=new ProcessBuilder("/system/bin/getprop",name).redirectErrorStream(true).start();
        String text=read(p.getInputStream()).trim();need(p.waitFor()==0,"Property read failed");return text;
    }
    private static Object callAttr(Class<?> pyObject,Object value,String name,Object... args) throws Exception {
        return pyObject.getMethod("callAttr",String.class,Object[].class).invoke(value,new Object[]{name,args});
    }
    private static Object dictionaryGet(Class<?> pyObject,Object dictionary,String key) throws Exception {
        return callAttr(pyObject,dictionary,"__getitem__",key);
    }
    private static void guards(ClassLoader loader) throws Exception {
        Class<?> config=Class.forName("org.telegram.messenger.BuildConfig",true,loader);
        need(config.getField("APP_ID").getInt(null)==0,"API ID not isolated");
        need("".equals(config.getField("APP_HASH").get(null)),"API hash not isolated");
        need(config.getField("ISOLATED_DIAGNOSTIC").getBoolean(null),"Diagnostic isolation false");
        Class<?> policy=Class.forName("org.telegram.messenger.BuildVariantPolicy",true,loader);
        for(String method:new String[]{"authenticationAllowed","telegramTransportAllowed","pushAllowed","translationAllowed","pluginsAllowed","sessionRestoreAllowed"})
            need(Boolean.FALSE.equals(policy.getMethod(method).invoke(null)),"External capability enabled");
    }
    private static void pluginEngineNotStarted(ClassLoader loader) throws Exception {
        Class<?> engine=Class.forName("app.exteraless.plugins.PythonPluginsEngine",false,loader);
        // Read state only, without constructing the engine or invoking ensureStarted.
        Field field=engine.getDeclaredField("instance");field.setAccessible(true);Object instance=field.get(null);
        need(instance==null || Boolean.FALSE.equals(engine.getMethod("isStarted").invoke(instance)),"Plugin engine started");
    }
    private File fixture(File dir,String source,String name,String expected) throws Exception {
        File target=new File(dir,name);need(!target.exists(),"Existing fixture rejected");
        try(InputStream in=getContext().getAssets().open(source);OutputStream out=new FileOutputStream(target)){
            byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);
        }
        need(sha(target).equals(expected),"Fixture hash mismatch");return target;
    }
    @Override public void onStart() {
        JSONObject report=new JSONObject();int exit=Activity.RESULT_CANCELED;
        try {
            JSONObject c=new JSONObject(asset("contract.json"));Context target=getTargetContext();
            String runId=args.getString("run_id",""),profile=args.getString("profile","");
            need(runId.matches("[0-9a-f]{32}"),"Invalid run nonce");
            need("true".equals(args.getString("clean_lab")),"Missing clean offline lab attestation");
            report.put("run_id",runId);report.put("profile",profile);report.put("status","BLOCKED");
            String arch=Os.uname().machine,bridge=property("ro.dalvik.vm.native.bridge");
            boolean emulator="1".equals(property("ro.kernel.qemu")) || "1".equals(property("ro.boot.qemu")) || property("ro.hardware").startsWith("cutf_");
            long page=Os.sysconf(OsConstants._SC_PAGESIZE);
            need(emulator && Process.is64Bit() && "aarch64".equals(arch) && Build.SUPPORTED_ABIS.length>0 && "arm64-v8a".equals(Build.SUPPORTED_ABIS[0]),"Native ARM64 emulator required");
            need(bridge.isEmpty()||"0".equals(bridge),"Native translation bridge rejected");
            boolean strict="false".equals(property("bionic.linker.16kb.app_compat.enabled")) || "fatal".equals(property("bionic.linker.16kb.app_compat.enabled"));
            strict=strict && "true".equals(property("pm.16kb.app_compat.disabled"));
            need(("api24-4k".equals(profile)&&Build.VERSION.SDK_INT==24&&page==4096)||("arm64-16k".equals(profile)&&Build.VERSION.SDK_INT>=35&&page==16384&&strict),"Incorrect API/page/compat profile");
            report.put("environment",new JSONObject().put("api",Build.VERSION.SDK_INT).put("page_size",page).put("abi",Build.SUPPORTED_ABIS[0]).put("arch",arch).put("native_bridge",bridge).put("emulator",emulator).put("clean_lab",true).put("strict_16k",strict));
            need(c.getString("target_package").equals(target.getPackageName()),"Wrong instrumentation target");
            need(sha(new File(target.getApplicationInfo().sourceDir)).equals(c.getString("apk_sha256")),"Installed APK digest mismatch");
            PackageManager pm=target.getPackageManager();PackageInfo pi=pm.getPackageInfo(target.getPackageName(),PackageManager.GET_SIGNATURES|PackageManager.GET_PERMISSIONS);
            need(pi.signatures!=null && pi.signatures.length==1,"Single signer required");
            String cert=hex(MessageDigest.getInstance("SHA-256").digest(pi.signatures[0].toByteArray()));
            need(cert.equals(c.getString("certificate_sha256")),"Wrong target lab certificate");
            PackageInfo own=pm.getPackageInfo(c.getString("runner_package"),PackageManager.GET_SIGNATURES|PackageManager.GET_PERMISSIONS);
            need(own.signatures!=null && own.signatures.length==1 && cert.equals(hex(MessageDigest.getInstance("SHA-256").digest(own.signatures[0].toByteArray()))),"Runner must use same diagnostic lab certificate");
            need(own.requestedPermissions==null||own.requestedPermissions.length==0,"Test APK must request no permissions");
            if(pi.requestedPermissions!=null)for(String permission:pi.requestedPermissions)
                need(permission.equals("android.permission.ACCESS_NETWORK_STATE")||permission.equals(c.getString("target_package")+".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"),"Unexpected Diagnostic permission");
            report.put("internet_absent",true);report.put("apk_sha256",c.getString("apk_sha256"));report.put("certificate_sha256",cert);
            ClassLoader loader=target.getClassLoader();guards(loader);pluginEngineNotStarted(loader);report.put("capabilities_closed",true);
            stage="launch";Intent launch=pm.getLaunchIntentForPackage(target.getPackageName());need(launch!=null,"No launch entrypoint");
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);Activity activity=startActivitySync(launch);need(activity!=null,"Activity did not start");waitForIdleSync();
            stage="jni";Class<?> nativeLoader=Class.forName("org.telegram.messenger.NativeLoader",true,loader);
            need(Boolean.TRUE.equals(nativeLoader.getMethod("loaded").invoke(null)),"Application JNI not loaded");report.put("jni_loaded",true);
            stage="chaquopy";Class<?> python=Class.forName("com.chaquo.python.Python",true,loader),pyObject=Class.forName("com.chaquo.python.PyObject",true,loader);
            need(Boolean.FALSE.equals(python.getMethod("isStarted").invoke(null)),"Python unexpectedly started before test");
            Class<?> platform=Class.forName("com.chaquo.python.Python$Platform",true,loader),androidPlatform=Class.forName("com.chaquo.python.android.AndroidPlatform",true,loader);
            // Explicit test-only runtime start. Never invokes plugins, preferences or native policy setters.
            python.getMethod("start",platform).invoke(null,androidPlatform.getConstructor(Context.class).newInstance(target.getApplicationContext()));
            need(Boolean.TRUE.equals(python.getMethod("isStarted").invoke(null)),"Chaquopy start failed");
            File dir=new File(target.getCacheDir(),"flexygram-native-lab-"+runId);need(dir.mkdir(),"Fresh fixture directory required");
            File cases=fixture(dir,"runtime_cases.py","runtime_cases.py",c.getString("runtime_cases_sha256"));
            File font=fixture(dir,"font.ttf","font.ttf",c.getString("font_sha256"));
            Object instance=python.getMethod("getInstance").invoke(null),builtins=python.getMethod("getModule",String.class).invoke(instance,"builtins");
            Object globals=callAttr(pyObject,builtins,"dict");callAttr(pyObject,builtins,"exec",asset("probe.py"),globals);
            Object function=dictionaryGet(pyObject,globals,"run_probe");
            String payload=new JSONObject().put("contract",c).put("cases_path",cases.getAbsolutePath()).put("font_path",font.getAbsolutePath()).toString();
            stage="functional";Object result=pyObject.getMethod("call",Object[].class).invoke(function,new Object[]{new Object[]{payload}});
            JSONObject functional=new JSONObject(result.toString());report.put("python",functional);
            guards(loader);pluginEngineNotStarted(loader);
            need(functional.getInt("tests_run")==12 && functional.getInt("failures")==0 && functional.getInt("errors")==0 && functional.getInt("skipped")==0 && functional.getInt("expected_failures")==0 && functional.getInt("unexpected_successes")==0,"Functional suite incomplete");
            report.put("status","PASS");exit=Activity.RESULT_OK;
        } catch(Throwable error) {
            try {
                Throwable cause=error instanceof InvocationTargetException && error.getCause()!=null ? error.getCause():error;
                report.put("status","BLOCKED");report.put("error_stage",stage);report.put("error_class",cause.getClass().getName());
                // No throwable messages, credentials or target preferences are copied into logs.
                JSONArray stack=new JSONArray();for(StackTraceElement frame:cause.getStackTrace())if(stack.length()<12)stack.put(frame.getClassName()+"."+frame.getMethodName()+":"+frame.getLineNumber());
                report.put("error_frames",stack);
            } catch(JSONException ignored) { }
        }
        Bundle results=new Bundle();results.putString("lab_result",report.toString());finish(exit,results);
    }
}
