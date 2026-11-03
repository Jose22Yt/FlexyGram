"""Product names, non-destructive storage compatibility and own-repository update selection."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import pytest
from test_composer_layout import method

ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/'TMessagesProj/src/main/java'
RES=ROOT/'TMessagesProj/src/main/res'


def compile_run(tmp_path,files,actual=()):
    if not shutil.which('java'):pytest.skip('JDK required')
    paths=[]
    for name,body in files.items():
        file=tmp_path/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(body);paths.append(file)
    r=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(tmp_path),*map(str,paths),*map(str,actual)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    r=subprocess.run(['java','-cp',str(tmp_path),'Probe',str(tmp_path)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr


def test_storage_default_migrates_without_moving_files_or_overwriting_custom_paths(tmp_path):
    compile_run(tmp_path,{
        'android/content/SharedPreferences.java':'''package android.content;public class SharedPreferences{public java.util.Map<String,Object>values=new java.util.HashMap<>();public int writes;public String getString(String k,String d){return (String)values.getOrDefault(k,d);}public Editor edit(){return new Editor();}public class Editor{public Editor putString(String k,String v){values.put(k,v);writes++;return this;}public void apply(){}}}''',
        'android/content/pm/PackageInfo.java':'package android.content.pm;public class PackageInfo{public long firstInstallTime,lastUpdateTime;}',
        'android/content/pm/PackageManager.java':'package android.content.pm;public class PackageManager{public PackageInfo info=new PackageInfo();public boolean fail;public PackageInfo getPackageInfo(String p,int f){if(fail)throw new RuntimeException();return info;}}',
        'android/content/Context.java':'package android.content;public class Context{public android.content.pm.PackageManager pm=new android.content.pm.PackageManager();public android.content.pm.PackageManager getPackageManager(){return pm;}public String getPackageName(){return "com.flexygram.messenger";}}',
        'Probe.java':'''import app.flexygram.branding.FlexyBranding;import android.content.*;import java.io.*;import java.nio.file.*;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args)throws Exception{
 SharedPreferences p=new SharedPreferences();FlexyBranding.migrateSaveFolder(p);check(p.writes==0);
 p.values.put("customSavePath","exteraless");FlexyBranding.migrateSaveFolder(p);check(p.values.get("customSavePath").equals("FlexyGram")&&p.writes==1);FlexyBranding.migrateSaveFolder(p);check(p.writes==1);
 for(String custom:new String[]{"Pictures/My files","", "Telegram", "exteraless/custom"}){p.values.put("customSavePath",custom);FlexyBranding.migrateSaveFolder(p);check(p.values.get("customSavePath").equals(custom)&&p.writes==1);}
 p.values.put("customSavePath",true);FlexyBranding.migrateSaveFolder(p);check(p.writes==1);
 Context c=new Context();c.pm.info.firstInstallTime=100;c.pm.info.lastUpdateTime=100;check(!FlexyBranding.isUpdatedInstallation(c));c.pm.info.lastUpdateTime=200;check(FlexyBranding.isUpdatedInstallation(c));c.pm.fail=true;check(!FlexyBranding.isUpdatedInstallation(c));
 File parent=new File(args[0],"storage");check(parent.mkdir());File brand=FlexyBranding.cacheDirectory(parent,"Telegram");check(brand.getName().equals("FlexyGram")&&!brand.exists());
 File old=new File(parent,"Telegram");check(old.mkdir());File media=new File(old,"existing.dat");Files.writeString(media.toPath(),"preserved");
 check(FlexyBranding.cacheDirectory(parent,"Telegram").equals(old));check(FlexyBranding.cacheDirectory(parent,"Telegram",false).equals(brand));
 check(Files.readString(media.toPath()).equals("preserved"));check(brand.mkdir());check(FlexyBranding.cacheDirectory(parent,"Telegram").equals(brand));check(media.exists());
 check(FlexyBranding.cacheDirectory(parent,"Telegram Images").getName().equals("FlexyGram Images"));
 check(FlexyBranding.cacheDirectory(parent,"FlexyGram Alpha").getName().equals("FlexyGram Alpha"));
 }}''',
    },[JAVA/'app/flexygram/branding/FlexyBranding.java'])
    config=(JAVA/'tw/nekomimi/nekogram/NekoConfig.java').read_text()
    assert 'addConfig("customSavePath", configTypeString, app.flexygram.branding.FlexyBranding.NAME)' in config
    assert config.index('FlexyBranding.migrateSaveFolder(getPreferences())')<config.index('for (int i = 0; i < configs.size(); i++)')
    media=(JAVA/'org/telegram/messenger/MediaController.java').read_text()
    assert not re.search(r'DIRECTORY_\w+\)?\s*,\s*"Telegram"',media)
    assert 'FlexyBranding.cacheDirectory' in (JAVA/'org/telegram/messenger/ImageLoader.java').read_text()
    # Lookup of existing absolute DB/document paths remains native and unmodified.
    loader=(JAVA/'org/telegram/messenger/FileLoader.java').read_text()
    assert 'return new File(document.localPath);' in loader and 'return new File(path);' in loader


def test_owned_strings_use_flexygram_and_legal_format_attribution_is_retained():
    keep={'FlexySettingsAboutBody','FlexySettingsCreditsBody','OEGeneralExportFormatExtera','OEGeneralImportEtgEmpty','OEAyuDatabaseImportInfo'}
    for file in RES.glob('values*/*.xml'):
        for entry in ET.parse(file).getroot():
            if entry.tag!='string':continue
            key=entry.get('name');text=''.join(entry.itertext())
            if key in {'AppName','NagramX','Nagram','OpenExtera','NekoSettings','N_Config'}:assert text=='FlexyGram',(file,key,text)
            if key=='AppNameBeta':assert text=='FlexyGram Beta'
            if key=='CloudConfigDesc':assert 'FlexyGram' in text
            if key not in keep:assert not re.search(r'exteraless|nagram(?: ?x)?',text,re.I),(file,key,text)
    base={e.get('name'):''.join(e.itertext()) for e in ET.parse(RES/'values/flexygram_settings_info.xml').getroot()}
    assert 'Exteraless' in base['FlexySettingsCreditsBody'] and 'GPL-3.0' in base['FlexySettingsCreditsBody']
    manifest=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml')
    assert manifest.find('application').get('{http://schemas.android.com/apk/res/android}label')=='@string/NagramX'
    locale=(JAVA/'org/telegram/messenger/LocaleController.java').read_text()
    names=method(locale,'private String getStringInternal(String key, String fallback, int fallbackRes, int res)')
    assert names.index('key.equals("NagramX")')<names.index('localeValues.get(key)')
    assert 'return app.flexygram.branding.FlexyBranding.NAME;' in method(locale,'public static String getAppName()')
    assert 'APP_PACKAGE=com.flexygram.messenger' in (ROOT/'gradle.properties').read_text()
    assert 'rootProject.name = "FlexyGram"' in (ROOT/'settings.gradle').read_text()
    about=(JAVA/'tw/nekomimi/nekogram/settings/NekoAboutActivity.java').read_text()
    assert 'https://github.com/Jose22Yt/FlexyGram' in about
    assert 'FlexySettingsCreditsBody' in about and 'openByUserName("NagramX"' not in about


def test_updater_targets_own_repo_and_rejects_upstream_or_other_variant_assets(tmp_path):
    source=(JAVA/'app/exteraless/updater/GitHubUpdater.java').read_text()
    assert 'REPO = "Jose22Yt/FlexyGram"' in source and 'PREFS = "flexygram_updater"' in source
    chooser=method(source,'private static JSONObject pickAsset(')
    compile_run(tmp_path,{'Probe.java':'''import java.util.*;
public class Probe{
 static class Build{static String[]SUPPORTED_ABIS={"arm64-v8a"};}static class BuildConfig{static boolean CONNECTED_ALPHA;}
 static class JSONObject{String name;JSONObject(String n){name=n;}String optString(String key){return name;}}
 static class JSONArray{List<JSONObject>v=new ArrayList<>();JSONArray(String...names){for(String n:names)v.add(new JSONObject(n));}int length(){return v.size();}JSONObject optJSONObject(int i){return v.get(i);}}
 CHOOSER
 public static void main(String[]args){
 JSONArray a=new JSONArray("exteraless-arm64-v8a.apk","FlexyGram-Alpha-arm64-v8a.apk","FlexyGram-Beta-arm64-v8a.apk");
 if(!pickAsset(a).name.equals("FlexyGram-Beta-arm64-v8a.apk"))throw new AssertionError();BuildConfig.CONNECTED_ALPHA=true;if(!pickAsset(a).name.equals("FlexyGram-Alpha-arm64-v8a.apk"))throw new AssertionError();
 if(pickAsset(new JSONArray("exteraless-universal.apk","notes.txt"))!=null)throw new AssertionError();
 }}'''.replace('CHOOSER',chooser)})


def test_actual_gradle_apk_name_expression_ignores_upstream_base_name(tmp_path):
    jar=os.environ.get('FLEXY_BRANDING_GROOVY_JAR','/tmp/flexy-branding-groovy.jar')
    if not Path(jar).is_file() or not shutil.which('java'):pytest.skip('Standalone Groovy needed; no Android/Gradle build is run')
    script=tmp_path/'names.groovy'
    script.write_text('''class Property {String value;void set(Object v){value=v.toString()}}
def source=new File(args[0]).text
def start=source.indexOf("            String gramName = ")
def end=source.indexOf("\\n        }\\n    }\\n}",start)
assert start>=0 && end>start
def code=source.substring(start,end)
for (boolean beta : [true,false]) for (def filters : [[],[[identifier:'arm64-v8a']],[[identifier:'arm64-v8a'],[identifier:'xxhdpi']]]) {
 def result=new Property(value:'exteraless-debug.apk')
 def binding=new Binding([beta:beta,BETA_VERSION_NAME:'13.0.2-beta1',BETA_VERSION_CODE:'1280',verName:'13.0.2',verCode:1280,
   variant:[name:beta?'debug':'connectedAlpha'],output:[filters:filters,outputFileName:result]])
 new GroovyShell(binding).evaluate(code)
 assert result.value.startsWith(beta?'FlexyGram-Beta-v13.0.2-beta1(1280)-debug':'FlexyGram-Alpha-v13.0.2(1280)-connectedAlpha')
 assert result.value.endsWith('.apk') && !result.value.toLowerCase().contains('exteraless')
 if(filters)assert result.value.endsWith('-'+filters.collect{it.identifier}.join('-')+'.apk')
}
''')
    result=subprocess.run(['java','-cp',jar,'groovy.ui.GroovyMain',str(script),str(ROOT/'TMessagesProj/build.gradle')],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
