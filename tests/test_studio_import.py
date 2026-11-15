"""Real Studio catalog/codec transactions and Android API contracts, without packaging an APK."""
import os
from pathlib import Path
import shutil
import subprocess
import pytest
from test_render_work_reuse import ROOT, JAVA, probe
from test_composer_layout import method


def studio_check(script):
    sdk=Path(os.environ.get('ANDROID_HOME','/workspace/.flexygram/android-sdk'))
    if not (sdk/'platforms/android-37.0/android.jar').is_file() or not shutil.which('javac'):
        pytest.skip('Android API37 and JDK required for isolated Studio check')
    env=dict(os.environ,ANDROID_HOME=str(sdk))
    result=subprocess.run(['python',str(ROOT/'tools/connected_alpha'/script)],cwd=ROOT,env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    return result.stdout


def test_complete_transfer_named_actions_selective_apply_and_scoped_undo():
    assert 'Studio client checks=' in studio_check('check_studio_client.py')


def test_all_studio_java_types_match_android_apis():
    assert 'type check passed' in studio_check('check_studio_types.py')


def test_saf_export_retries_unsupported_or_null_truncate_stream(tmp_path):
    production=(JAVA/'app/flexygram/studio/FlexyStudioFiles.java').read_text()
    body=method(production,'static OutputStream openForExport(')
    probe(tmp_path,{'Probe.java':'''import java.io.*;public class Probe{
 static class Uri{}static class ContentResolver{
 int calls,mode;OutputStream expected=new ByteArrayOutputStream();OutputStream openOutputStream(Uri u,String access)throws IOException{
 calls++;if(calls==1){if(!access.equals("wt"))throw new AssertionError();if(mode==0)return null;if(mode==1)throw new FileNotFoundException();if(mode==2)throw new IllegalArgumentException();if(mode==3)return expected;throw new IOException("fault");}
 if(!access.equals("w"))throw new AssertionError();return expected;}}
 BODY
 public static void main(String[]args)throws Exception{
 for(int mode=0;mode<4;mode++){ContentResolver r=new ContentResolver();r.mode=mode;if(openForExport(r,new Uri())!=r.expected||r.calls!=(mode==3?1:2))throw new AssertionError();}
 ContentResolver r=new ContentResolver();r.mode=4;try{openForExport(r,new Uri());throw new AssertionError();}catch(IOException expected){if(r.calls!=1)throw new AssertionError();}
 }}'''.replace('BODY',body)})


def test_trial_has_no_studio_file_association():
    import xml.etree.ElementTree as ET
    ns='{http://schemas.android.com/apk/res/android}'
    root=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot()
    for item in root.iter('data'):
        assert '.flexygram' not in item.get(ns+'pathPattern','').lower()
        assert 'application/vnd.flexygram.configuration' not in item.get(ns+'mimeType','')
