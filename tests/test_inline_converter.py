"""Executes production Java core, host lifecycle doubles and integration source contracts.
Host timing/doubles do not establish Android compilation, rendering or physical performance.
"""
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import pytest
ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/'TMessagesProj/src/main/java'
CORE=JAVA/'app/flexygram/inlineconverter'
PURE=['InlineConversionMatch','InlineConversionScanner','UnitConversionEngine','TimeConversionEngine','InlineConversionCache','ExchangeRateProvider']
@pytest.fixture(scope='module')
def compiled(tmp_path_factory):
 out=tmp_path_factory.mktemp('converter-java')
 command=['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(out)]+[str(CORE/(n+'.java'))for n in PURE]+[str(ROOT/'tests/inline_converter/CoreProbe.java')]
 result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
 return out
@pytest.mark.parametrize('case',['scanner','numbers','reserved','limits','units','time','dst','cache','provider','benchmark'])
def test_production_core(compiled,case):
 run=subprocess.run(['java','-cp',str(compiled),'CoreProbe',case],capture_output=True,text=True)
 assert run.returncode==0,run.stderr
 print(run.stdout)
def method(s,anchor):
 a=s.index(anchor);i=s.index('{',a)+1;depth=1
 while depth:depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def test_native_precedence_and_lifecycle():
 cell=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
 touch=method(cell,'public boolean onTouchEvent(MotionEvent event)')
 assert touch.index('checkTextSelection(event)')<touch.index('checkInlineConversionTouch(event)')
 for handler in ['checkSpoilersMotionEvent','checkTextBlockMotionEvent','checkCaptionMotionEvent','checkReactionsTouchEvent','checkReplyTouchEvent','checkAdminTouchEvent']:
  assert touch.index(handler)<touch.index('checkInlineConversionTouch(event)')
 for hook in ['public void onAttachedToWindow()','private void setMessageContent(MessageObject messageObject,']:
  assert 'prepareInlineConversions();' in method(cell,hook)
 assert 'inlineConversion.release()'in method(cell,'protected void onDetachedFromWindow()')
 assert 'inlineConversion.cancelGesture()'in method(cell,'protected boolean onLongPress()')
 assert 'block.code || block.quote || !block.spoilers.isEmpty()'in method(cell,'private int inlineConversionOffset(')
 assert 'block.charactersOffset + block.textLayout.getOffsetForHorizontal' in cell
 # None of the native text/link/caption logic was rewritten.
 old=subprocess.check_output(['git','show','abf93053f9f98bae95b88f070f3e964c8b3bb311:TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java'],cwd=ROOT,text=True)
 for name in ['checkTextBlockMotionEvent','checkCaptionMotionEvent','checkTextSelection','checkReactionsTouchEvent']:
  # Locate method declaration rather than an earlier call site.
  anchor='private boolean '+name+'('
  assert method(cell,anchor)==method(old,anchor)
def test_no_draw_detection_or_network_or_message_mutation():
 all_source='\n'.join(p.read_text()for p in CORE.glob('*.java'))
 for forbidden in ['HttpURLConnection','OkHttp','new Thread(','ScheduledExecutor','postDelayed(','.setSpan(','messageText =','OVERLAY','file://','System.out.print']:
  assert forbidden not in all_source
 controller=(CORE/'InlineConversionController.java').read_text()
 for required in ['Utilities.globalQueue.postRunnable','Utilities.globalQueue.cancelRunnable','WeakReference','c.generation!=token','config.revision','ClickableSpan','URLSpanMono','FLAG_STYLE_SPOILER']:
  assert required in controller
 assert 'InlineConversionScanner.scan'not in method(controller,'public boolean touch(')
 assert 'InlineConversionScanner.scan'not in method(controller,'public void observe(')
 assert 'onDraw('not in all_source
 config=(CORE/'InlineConversionConfig.java').read_text();assert 'getBoolean(ENABLED,false)'in config
 assert 'NekoConfig.getPreferences()'in config
 assert 'key.equals(TARGET_ZONE)'in config and 'ZoneId.of' in config
 assert 'SharedPreferences.Editor' in config and 'e.apply();current=new Snapshot' in config
 popover=(CORE/'InlineConversionPopover.java').read_text()
 for required in ['getWindowVisibleDisplayFrame','getPaddingTop','getPaddingBottom','getLocationOnScreen','getLocationInWindow','removeOnGlobalLayoutListener','removeOnScrollChangedListener','TimeConversionEngine.convert','DatePickerDialog','InlineConversionCurrencyUnavailable']:
  assert required in popover
 assert 'ExchangeRateProvider' not in popover
 assert 'if(result!=null)' in popover

def test_direct_settings_single_owner_and_translation_parity():
 registry=JAVA/'app/flexygram/settings/signature'
 page=(registry/'SignatureDirectSettingsActivity.java').read_text()
 assert page.count('new app.flexygram.inlineconverter.InlineConversionSettingsSection()')==1
 assert page.index('case "chat":')<page.index('new app.flexygram.inlineconverter.InlineConversionSettingsSection()')<page.index('case "home":')
 assert 'InlineConversionSettingsSection' in (registry/'Settings3Registry.java').read_text()
 section=(CORE/'InlineConversionSettingsSection.java').read_text()
 for key in ['ENABLED','CURRENCY','TARGET_CURRENCY','TIME','TARGET_ZONE','UNITS','SYSTEM']:assert section.count('addRow(InlineConversionConfig.'+key+')')==1
 translations=[]
 for locale in ['values','values-es','values-ru']:
  root=ET.parse(ROOT/'TMessagesProj/src/main/res'/locale/'inline_converter.xml').getroot()
  names=[e.attrib['name']for e in root];assert len(names)==len(set(names))
  assert all(e.text for e in root);translations.append(set(names))
 assert translations[0]==translations[1]==translations[2]

@pytest.fixture(scope='module')
def controller_host(tmp_path_factory):
 import importlib.util
 out=tmp_path_factory.mktemp('converter-hosts')
 spec=importlib.util.spec_from_file_location('converter_hosts',ROOT/'tests/inline_converter/hosts.py');hosts=importlib.util.module_from_spec(spec);spec.loader.exec_module(hosts);hosts.write(out)
 files=[str(p)for p in out.rglob('*.java')]+[str(CORE/(n+'.java'))for n in PURE+['InlineConversionConfig','InlineConversionController']]+[str(ROOT/'tests/inline_converter/ControllerProbe.java')]
 result=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(out),*files],capture_output=True,text=True);assert result.returncode==0,result.stderr
 return out
@pytest.mark.parametrize('case',['edits','cancel','gestures','settings','spans'])
def test_controller_with_explicit_host_doubles(controller_host,case):
 result=subprocess.run(['java','-cp',str(controller_host),'ControllerProbe',case],capture_output=True,text=True)
 assert result.returncode==0,result.stderr
 print(result.stdout)

def test_identity_and_distribution_inputs_are_unchanged():
 for name in ['TMessagesProj/src/main/AndroidManifest.xml','TMessagesProj/build.gradle','gradle.properties','gradle/flexygram-beta.gradle']:
  original=subprocess.check_output(['git','show','abf93053f9f98bae95b88f070f3e964c8b3bb311:'+name],cwd=ROOT)
  assert (ROOT/name).read_bytes()==original,name
