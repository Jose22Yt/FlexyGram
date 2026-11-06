#!/usr/bin/env python3
"""JVM round trips of production Studio backup/catalog/codec/transaction. No APK or Android packaging."""
import os,sys,subprocess,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'studio_native'))
from stubs import write_stubs
ROOT=Path(__file__).resolve().parents[2]
SDK=Path(os.environ.get('ANDROID_HOME',str(ROOT.parent/'.flexygram/android-sdk')))/'platforms/android-37.0/android.jar'
with tempfile.TemporaryDirectory(prefix='studio-client-') as tmp:
 src=Path(tmp)/'src';src.mkdir();write_stubs(src,ROOT)
 # Keep production client logic and declared native API doubles, not Android UI classes.
 keep={'StudioImportPlan.java','StudioClientBackup.java','StudioClientCatalog.java','StudioCodec.java','StudioSchema.java','StudioTransaction.java','ConfigItem.java','NekoConfig.java','NaConfig.java','OpenExteraConfig.java','AppearanceConfig.java','ChatsConfig.java','GeneralConfig.java','IconPacksConfig.java','PillStackConfig.java','UtilsConfig.java','SharedConfig.java','LiteMode.java','LauncherIconController.java','BubbleInteractionSettings.java','InlineConversionConfig.java','LiquidNavigationConfig.java','SignatureSmartPreviews.java','BubbleConfig.java','HeaderConfig.java','GlyphConfig.java','IconPackManager.java'}
 for p in src.rglob('*.java'):
  if p.name not in keep:p.unlink()
 def put(path,data):
  p=src/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
 put('app/flexygram/animation/FastMotionConfig.java','package app.flexygram.animation;public class FastMotionConfig{public static void load(){}}')
 put('android/content/Context.java','package android.content;public class Context{public static final int MODE_PRIVATE=0;public SharedPreferences getSharedPreferences(String f,int m){return app.flexygram.studio.StudioClientTest.preferences(f);}}')
 put('android/os/Looper.java','package android.os;public class Looper{private static final Looper MAIN=new Looper();public static Looper myLooper(){return MAIN;}public static Looper getMainLooper(){return MAIN;}}')
 put('android/util/Base64.java','package android.util;public class Base64{public static final int DEFAULT=0;public static String encodeToString(byte[] b,int f){return java.util.Base64.getEncoder().encodeToString(b);}}')
 put('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();}')
 put('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities{public static void runOnUIThread(Runnable r){r.run();}}')
 put('org/telegram/ui/LauncherIconController.java','package org.telegram.ui;public class LauncherIconController{public enum LauncherIcon{EXTERALESS,FLEX_GREEN};public static LauncherIcon active=LauncherIcon.FLEX_GREEN;public static boolean isEnabled(LauncherIcon i){return i==active;}public static void setIcon(LauncherIcon i){active=i;}}')
 put('app/flexygram/studio/StudioClientTheme.java','package app.flexygram.studio;public class StudioClientTheme{public static Object snapshot(){return java.util.Map.of("colors",java.util.Map.of("test",1L));}public static void validate(Object v){}public static void apply(Object v){}}')
 put('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController{public static LocaleController getInstance(){return new LocaleController();}public Object getLanguageFromDict(String code){return new Object();}public void reloadStudioLanguage(){}}')
 p=src/'tw/nekomimi/nekogram/NekoConfig.java';s=p.read_text().replace('public static java.util.List<tw.nekomimi.nekogram.config.ConfigItem> getStudioItems(){return java.util.List.of();}', 'public static final java.util.List<tw.nekomimi.nekogram.config.ConfigItem> items=new java.util.ArrayList<>();public static java.util.List<tw.nekomimi.nekogram.config.ConfigItem> getStudioItems(){return items;}');p.write_text(s)
 put('app/flexygram/studio/FlexyStudioStore.java','package app.flexygram.studio;import app.flexygram.studio.core.*;public class FlexyStudioStore{public static void validate(StudioCodec.Preset p){if(p.sections.containsKey("client"))StudioClientBackup.validate((String)p.sections.get("client").get("settings"));}static Object readPreference(android.content.SharedPreferences p,StudioSchema.Key k){if(k.defaultValue instanceof Integer)return p.getInt(k.preference,(Integer)k.defaultValue);if(k.defaultValue instanceof Boolean)return p.getBoolean(k.preference,(Boolean)k.defaultValue);return p.getString(k.preference,(String)k.defaultValue);}}')
 test=ROOT/'tools/connected_alpha/studio_native/StudioClientTest.java'
 subprocess.run([os.environ.get('JAVAC','javac'),'-encoding','UTF-8','-proc:none','-cp',str(SDK),'-d',tmp+'/classes',*map(str,src.rglob('*.java')),str(test)],check=True)
 subprocess.run([os.environ.get('JAVA','java'),'-cp',tmp+'/classes:'+str(SDK),'app.flexygram.studio.StudioClientTest'],check=True)
