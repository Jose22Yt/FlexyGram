"""Exact continuation/security/structural cost checks; Android/server/device evidence is separate."""
from pathlib import Path
import subprocess,tempfile,unittest,xml.etree.ElementTree as ET
import alpha1283_contract as audit
from integration1284_contract import historical_bytes
from reconstruction1285_contract import prior_bytes

ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
class Alpha1283(unittest.TestCase):
 def test_exact_review_and_all_unknown_mutations_rejected(self):
  audit.verify_current()
  for path in audit.spec()['reviewed']:
   raw=historical_bytes(path)+b'\nUNREVIEWED'
   self.assertEqual(raw,audit.restore(path,raw),path)
 def test_release_gates_only_increment_the_installed_checkpoint_version(self):
  for path in ['TMessagesProj/build.gradle','.github/workflows/connected-alpha-arm64.yml','tools/connected_alpha/build_private_apk.py']:
   before=audit.original(path);now=historical_bytes(path)
   self.assertIn(b'1283',now);self.assertEqual(before,now.replace(b'1283',b'1282'),path)
 def test_auth_protocol_core_navigation_media_and_approved_header_are_unchanged(self):
  names=['org/telegram/ui/ActionBar/ActionBarLayout.java','org/telegram/ui/ActionBar/ActionBarPopupWindow.java','org/telegram/ui/Cells/ChatMessageCell.java','org/telegram/messenger/SendMessagesHelper.java','org/telegram/messenger/MediaController.java','org/telegram/ui/LoginActivity.java','org/telegram/ui/Components/ChatActivityEnterView.java','org/telegram/ui/Components/FilterTabsView.java','org/telegram/ui/ActionBar/MessageDrawable.java','app/flexygram/bubbles/SignatureWallpaperBlur.java','app/flexygram/header/SignatureChatHeader.java','app/flexygram/header/HeaderConfig.java']
  for path in names:
   n='TMessagesProj/src/main/java/'+path;self.assertEqual(audit.original(n),historical_bytes(n),n)
 def test_sticker_metadata_takes_the_real_uploaded_document_path_and_waits_for_server(self):
  sender=prior_bytes('TMessagesProj/src/main/java/app/flexygram/bubbles/interaction/NativeBubbleStickerSender.java').decode()
  host=prior_bytes('TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java').decode();start=host.index('private boolean canUseFlexyBubbleSticker(');end=host.index('/** Native menu policy',start);hook=host[start:end]
  self.assertIn('SendMessagesHelper.SendMessageParams.of(',hook);self.assertIn('file.getAbsolutePath(),dialog',hook)
  self.assertIn('NativeBubbleStickerSender.send(account,request,file,result)',hook)
  for token in ['getSendPaidMessagesStars(dialog_id)>0','getSlowModeTimer()!=null','currentAccount!=account','ChatObject.canSendStickers','lastMessageMenuStatus.allowCopy && lastMessageMenuStatus.allowForward']:
   self.assertIn(token,hook)
  for token in ['NotificationCenter.messageReceivedByServer','localId == 0','eventAccount != account','message.id > 0','document.id != 0','removeObserver','cancelRunOnUIThread']:
   self.assertIn(token,sender)
  self.assertNotIn('sendPhoto(',hook+sender);self.assertNotIn('prepareSendingDocument(',hook+sender)
  native=(JAVA/'org/telegram/messenger/SendMessagesHelper.java').read_text();start=native.index('} else if (type == 8) {',native.index('public void sendMessage(SendMessageParams'));block=native[start:start+2100]
  self.assertIn('uploadedDocument.attributes = document.attributes',block);self.assertIn('uploadedDocument.mime_type = document.mime_type',block)
 def test_only_on_demand_capture_workers_and_no_cancelled_engine(self):
  folder=JAVA/'app/flexygram/bubbles/interaction'
  for p in folder.glob('*.java'):
   s=p.read_text();self.assertNotIn('app.flexygram.motion',s);self.assertNotIn('FlexyFrameMotion',s)
  # Alpha1285 deliberately omitted single-tap animation. Alpha1286 adds a cell-local
  # controller by explicit owner request; the cancelled global engine stays forbidden.
  self.assertEqual(b'',__import__('interaction1286_contract').original('TMessagesProj/src/main/java/app/flexygram/bubbles/interaction/BubbleTapMotion.java'))
  workflow=prior_bytes('TMessagesProj/src/main/java/app/flexygram/bubbles/interaction/BubbleStickerWorkflow.java').decode();self.assertIn('new ArrayBlockingQueue<>(2)',workflow);self.assertIn('WORKER.allowCoreThreadTimeOut(true)',workflow)
  self.assertIn('sending || submitted',workflow);self.assertIn('!owner.sending',workflow)
  self.assertIn('if (!submitted && readyFile != null) readyFile.delete()',workflow)
 def test_export_is_saf_bounded_local_and_temporary(self):
  s=prior_bytes('TMessagesProj/src/main/java/app/flexygram/bubbles/interaction/BubbleStickerExport.java').decode()
  for token in ['Intent.ACTION_CREATE_DOCUMENT','Intent.CATEGORY_OPENABLE','content','BubbleStickerSpec.MAX_BYTES','generation.incrementAndGet()','try(OutputStream']:
   self.assertIn(token,s)
  for bad in ['MANAGE_EXTERNAL_STORAGE','file://','http://','https://','sendRequest','persistableUriPermission']:
   self.assertNotIn(bad,s)
 def test_settings_has_a_real_route_and_no_duplicate_or_motion_preferences(self):
  s=(JAVA/'app/exteraless/settings/OpenExteraChatsActivity.java').read_text();start=s.index('private void updateSignatureHubRows()');end=s.index('private void updateStickerRows()',start)
  self.assertIn('flexyContextPanelRow = addRow',s[start:end]);self.assertIn('new app.flexygram.bubbles.interaction.BubbleInteractionSettingsActivity()',s)
  prefs=(JAVA/'app/flexygram/bubbles/interaction/BubbleInteractionSettings.java').read_text();self.assertIn('"flexy_bubble_interaction"',prefs);self.assertIn('STYLE_KEY = "interaction_style"',prefs)
  settings=(JAVA/'app/flexygram/bubbles/interaction/BubbleInteractionSettingsActivity.java').read_text();self.assertIn('SignatureMatteSettingsActivity',settings);self.assertIn('BubbleInteractionSettings.setStyle(context, which)',settings);self.assertNotIn('Slider',settings)
 def test_es_en_ru_have_matching_user_visible_labels(self):
  sets=[]
  for locale in ['values','values-es','values-ru']:
   root=ET.fromstring(prior_bytes('TMessagesProj/src/main/res/'+locale+'/flexy_context_panel.xml'));items={x.get('name'):x.text for x in root};self.assertEqual(len(root),len(items));self.assertTrue(all(items.values()));sets.append(set(items))
  self.assertEqual(sets[0],sets[1]);self.assertEqual(sets[0],sets[2]);self.assertIn('FlexyContextSave',sets[0])
 def test_layout_metrics_move_out_of_repeated_draw_without_retaining_a_layout(self):
  s=(JAVA/'org/telegram/ui/Cells/DialogCell.java').read_text();a=s.index('private void drawSmartPreviewBackground(');b=s.index('private StaticLayout typingLayout;',a);draw=s[a:b]
  self.assertNotIn('getPrimaryHorizontal(',draw);self.assertNotIn('new ',draw)
  a=s.index('private void prepareSmartPreviewMetrics(');b=s.index('private final app.flexygram.home.SignatureSmartPreviewPalette',a);bind=s[a:b]
  self.assertEqual(2,bind.count('getPrimaryHorizontal('));self.assertIn('prepareSmartPreviewMetrics();\n        animatedEmojiStack',s)
  self.assertIn('smartPreviewMetricsReady=false',bind)
 def test_pure_sticker_spec_rejects_oversize_truncated_and_unsupported_sources(self):
  probe='''import app.flexygram.bubbles.interaction.*;public class StickerSpecProbe{static void ok(boolean v){if(!v)throw new AssertionError();}public static void main(String[]a){for(int w:new int[]{1,100,512,4096})for(int h:new int[]{1,100,512,4096}){try{var d=BubbleStickerSpec.dimensions(w,h);ok(Math.max(d[0],d[1])==512);ok(Math.max(w,h)<=Math.min(w,h)*4L);}catch(IllegalArgumentException e){ok(Math.max(w,h)>Math.min(w,h)*4L);}}byte[] b=new byte[24];byte[] magic="RIFF".getBytes();System.arraycopy(magic,0,b,0,4);System.arraycopy("WEBPVP8L".getBytes(),0,b,8,8);b[4]=16;ok(BubbleStickerSpec.isWebp(b));b[4]=17;ok(!BubbleStickerSpec.isWebp(b));ok(!BubbleStickerSpec.isWebp(null));ok(!BubbleStickerSpec.isWebp(new byte[524289]));ok(!BubbleTouchPolicy.mayConvertToSticker(true,true,true,false,false,true,true));ok(!BubbleTouchPolicy.mayConvertToSticker(true,true,false,true,false,true,true));ok(!BubbleTouchPolicy.mayConvertToSticker(true,true,false,false,true,true,true));}}'''
  with tempfile.TemporaryDirectory()as temp:
   p=Path(temp)/'StickerSpecProbe.java';p.write_text(probe);folder=Path(temp);
   for name in ['BubbleStickerSpec','BubbleTouchPolicy']:(folder/(name+'.java')).write_bytes(prior_bytes('TMessagesProj/src/main/java/app/flexygram/bubbles/interaction/'+name+'.java'))
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',temp,str(folder/'BubbleStickerSpec.java'),str(folder/'BubbleTouchPolicy.java'),str(p)],check=True,capture_output=True);subprocess.run(['java','-cp',temp,'StickerSpecProbe'],check=True,capture_output=True)
if __name__=='__main__':unittest.main()
