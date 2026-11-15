"""Compile production sticker transport and SAF export; no Telegram/network/device access."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def platform():
    return {
        'android/app/Activity.java': 'package android.app;public class Activity{public static final int RESULT_OK=-1;}',
        'android/net/Uri.java': 'package android.net;public class Uri{public String scheme="content";public String getScheme(){return scheme;}}',
        'android/content/Intent.java': '''package android.content;public class Intent{
 public static final String ACTION_CREATE_DOCUMENT="create",CATEGORY_OPENABLE="openable",EXTRA_TITLE="title";
 public String action,type,category,title;public android.net.Uri uri;public Intent(String a){action=a;}
 public Intent addCategory(String c){category=c;return this;}public Intent setType(String t){type=t;return this;}
 public Intent putExtra(String k,String v){title=v;return this;}public Intent setData(android.net.Uri u){uri=u;return this;}public android.net.Uri getData(){return uri;}}
''',
        'android/content/ContentResolver.java': '''package android.content;public class ContentResolver{
 public int deletions;public java.io.OutputStream openOutputStream(android.net.Uri uri,String mode)throws java.io.IOException{return new java.io.ByteArrayOutputStream();}}
''',
        'android/content/Context.java': '''package android.content;public class Context{public ContentResolver resolver=new ContentResolver();public ContentResolver getContentResolver(){return resolver;}}''',
        'android/provider/DocumentsContract.java': '''package android.provider;public class DocumentsContract{public static boolean deleteDocument(android.content.ContentResolver r,android.net.Uri u){r.deletions++;return true;}}''',
        'org/telegram/messenger/ApplicationLoader.java': '''package org.telegram.messenger;public class ApplicationLoader{public static final android.content.Context applicationContext=new android.content.Context();}''',
        'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger;public class AndroidUtilities{
 public static final java.util.concurrent.ConcurrentLinkedQueue<Runnable> ui=new java.util.concurrent.ConcurrentLinkedQueue<>();public static final java.util.List<Runnable> timers=new java.util.ArrayList<>();
 public static void runOnUIThread(Runnable r){ui.add(r);}public static void runOnUIThread(Runnable r,long d){timers.add(r);}public static void cancelRunOnUIThread(Runnable r){ui.remove(r);timers.remove(r);}}
''',
        'org/telegram/messenger/FileLog.java': 'package org.telegram.messenger;public class FileLog{public static void e(Throwable t){}}',
        'org/telegram/messenger/LocaleController.java': 'package org.telegram.messenger;public class LocaleController{public static String getString(int r){return "result";}}',
        'org/telegram/messenger/R.java': '''package org.telegram.messenger;public class R{public static class string{public static final int FlexyStickerExported=1,ErrorOccurred=2;}public static class drawable{public static final int msg_sticker_remix=1;}}''',
        'org/telegram/ui/ActionBar/BaseFragment.java': '''package org.telegram.ui.ActionBar;public class BaseFragment{
 public boolean isFinished,throwLaunch,missingParent;public android.content.Intent launched;public int request;
 public Object getParentActivity(){return missingParent?null:new Object();}public Object getParentLayout(){return missingParent?null:new Object();}
 public void startActivityForResult(android.content.Intent i,int code){if(throwLaunch)throw new IllegalStateException();launched=i;request=code;}}
''',
        'org/telegram/ui/Components/BulletinFactory.java': '''package org.telegram.ui.Components;public class BulletinFactory{
 public static int successes,errors;boolean error;public static boolean canShowBulletin(Object o){return true;}public static BulletinFactory of(Object o){return new BulletinFactory();}
 public BulletinFactory createSimpleBulletin(int i,String s){return this;}public BulletinFactory createErrorBulletin(String s){error=true;return this;}public void show(){if(error)errors++;else successes++;}}
''',
        'org/telegram/tgnet/TLRPC.java': '''package org.telegram.tgnet;public class TLRPC{public static class Chat{}public static class Document{}public static class TL_document extends Document{}public static class Message{public String attachPath;public Media media;}public static class Media{public Document document;}}''',
        'org/telegram/messenger/ChatObject.java': '''package org.telegram.messenger;public class ChatObject{public static boolean isForum(org.telegram.tgnet.TLRPC.Chat chat){return chat!=null;}}''',
        'org/telegram/messenger/MessageObject.java': '''package org.telegram.messenger;public class MessageObject{long dialog;int id;public org.telegram.tgnet.TLRPC.Message messageOwner=new org.telegram.tgnet.TLRPC.Message();public MessageObject(long d,int i,String path){dialog=d;id=i;messageOwner.attachPath=path;}public long getDialogId(){return dialog;}public int getId(){return id;}}''',
        'org/telegram/messenger/UserConfig.java': '''package org.telegram.messenger;public class UserConfig{public static UserConfig instance=new UserConfig();public long owner=7;public boolean active=true;public static UserConfig getInstance(int a){return instance;}public long getClientUserId(){return owner;}public boolean isClientActivated(){return active;}}''',
        'org/telegram/messenger/NotificationCenter.java': '''package org.telegram.messenger;import java.util.*;public class NotificationCenter{
 public static final int didReceiveNewMessages=1,messageReceivedByServer=2,messageSendError=3;
 public interface NotificationCenterDelegate{void didReceivedNotification(int event,int account,Object...args);}
 static NotificationCenter instance=new NotificationCenter();Map<Integer,Set<NotificationCenterDelegate>> observers=new HashMap<>();
 public static NotificationCenter getInstance(int a){return instance;}
 public void addObserver(NotificationCenterDelegate d,int event){observers.computeIfAbsent(event,k->new HashSet<>()).add(d);}
 public void removeObserver(NotificationCenterDelegate d,int event){Set<NotificationCenterDelegate>s=observers.get(event);if(s!=null)s.remove(d);}
 public void post(int event,Object...args){for(var d:new ArrayList<>(observers.getOrDefault(event,Collections.emptySet())))d.didReceivedNotification(event,0,args);}
 public int size(){int n=0;for(var s:observers.values())n+=s.size();return n;}}
''',
        'org/telegram/messenger/MediaDataController.java': '''package org.telegram.messenger;public class MediaDataController{public static final int TYPE_FAVE=1;public static int favorites;public static MediaDataController getInstance(int a){return new MediaDataController();}public void addRecentSticker(int type,Object q,org.telegram.tgnet.TLRPC.Document d,int now,boolean flag){favorites++;}}''',
        'app/flexygram/stickers/FlexyStickerMetadata.java': '''package app.flexygram.stickers;public class FlexyStickerMetadata{public static boolean isNativeStaticSticker(org.telegram.tgnet.TLRPC.Document d){return d!=null;}}''',
        'org/telegram/ui/ChatActivity.java': '''package org.telegram.ui;public class ChatActivity extends org.telegram.ui.ActionBar.BaseFragment{
 public long dialog=-10,mono=99,topicId=123;public int account;public boolean schedule;public org.telegram.messenger.MessageObject thread,reply;
 public Object quote=new Object(),arguments=new Object(),suggestion=new Object();
 public int getCurrentAccount(){return account;}public long getDialogId(){return dialog;}
 public long getTopicId(){return topicId;}public org.telegram.tgnet.TLRPC.Chat getCurrentChat(){return new org.telegram.tgnet.TLRPC.Chat();}
 public org.telegram.messenger.MessageObject getThreadMessage(){return thread;}public org.telegram.messenger.MessageObject getReplyMessage(){return reply;}
 public Object getReplyQuote(){return quote;}public Object getMessageChatSendParams(){return arguments;}public long getSendMonoForumPeerId(){return mono;}
 public Object getSendMessageSuggestionParams(){return suggestion;}public boolean isInScheduleMode(){return schedule;}}
''',
        'org/telegram/ui/Components/AlertsCreator.java': '''package org.telegram.ui.Components;public class AlertsCreator{
 public interface Delegate{void run(boolean notify,int date,int repeat);}public static Delegate selected;public static Runnable cancelled;
 public static Object createScheduleDatePickerDialog(Object context,long dialog,Delegate d,Runnable cancel,Object provider){selected=d;cancelled=cancel;return null;}}
''',
        'org/telegram/messenger/SendMessagesHelper.java': '''package org.telegram.messenger;import org.telegram.tgnet.TLRPC;public class SendMessagesHelper{
 public static SendMessageParams sent;public static int sends,oldId=-1;public static boolean fail;
 public static SendMessagesHelper getInstance(int a){return new SendMessagesHelper();}
 public static class SendMessageParams{public MessageObject replyToMsg,replyToTopMsg;public Object replyQuote,sendMessageChatArguments,suggestionParams;public long monoForumPeer,peer;public String path;public boolean notify;public int scheduleDate,scheduleRepeatPeriod;
 public static SendMessageParams of(TLRPC.TL_document d,Object v,String path,long peer,MessageObject reply,MessageObject top,Object c,Object e,Object markup,Object p,boolean notify,int date,int repeat,int ttl,Object parent,Object animation,boolean order){var r=new SendMessageParams();r.replyToMsg=reply;r.replyToTopMsg=top;r.path=path;r.peer=peer;r.notify=notify;r.scheduleDate=date;r.scheduleRepeatPeriod=repeat;return r;}}
 public void sendMessage(SendMessageParams p){sent=p;sends++;if(fail)throw new IllegalStateException();var m=new MessageObject(p.peer,oldId,p.path);NotificationCenter.getInstance(0).post(NotificationCenter.didReceiveNewMessages,p.peer,new java.util.ArrayList<>(java.util.List.of(m)));}
 public static void ack(){var m=new TLRPC.Message();m.media=new TLRPC.Media();m.media.document=new TLRPC.TL_document();NotificationCenter.getInstance(0).post(NotificationCenter.messageReceivedByServer,oldId,100,m,sent.peer);}
}
''',
    }


def test_forum_reply_favorites_schedule_and_retry_file_ownership(tmp_path):
    files = platform()
    files['Probe.java'] = '''import java.io.*;import java.nio.file.*;import app.flexygram.stickers.*;import org.telegram.messenger.*;import org.telegram.tgnet.TLRPC;import org.telegram.ui.ChatActivity;import org.telegram.ui.Components.AlertsCreator;
public class Probe{
 static int yes,no;static FlexyStickerSender.Callback callback=new FlexyStickerSender.Callback(){public void onSuccess(TLRPC.Document d){yes++;}public void onError(Throwable e){no++;}};
 static File file()throws Exception{File f=File.createTempFile("sticker-send-",".webp");Files.write(f.toPath(),new byte[]{1});return f;}
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args)throws Exception{
  ChatActivity owner=new ChatActivity();owner.thread=new MessageObject(-10,123,null);var doc=new TLRPC.TL_document();File f=file();
  FlexyStickerSender.send(owner,f,doc,false,callback);var p=SendMessagesHelper.sent;
  check(p.peer==-10&&p.replyToTopMsg==owner.thread&&p.replyToMsg==owner.thread&&p.monoForumPeer==99);
  check(p.replyQuote==owner.quote&&p.sendMessageChatArguments==owner.arguments&&p.suggestionParams==owner.suggestion&&f.isFile());
  check(NotificationCenter.getInstance(0).size()==3);SendMessagesHelper.ack();check(yes==1&&!f.exists()&&NotificationCenter.getInstance(0).size()==0&&AndroidUtilities.timers.isEmpty());
  owner.reply=new MessageObject(-10,125,null);f=file();FlexyStickerSender.send(owner,f,doc,false,callback);
  check(SendMessagesHelper.sent.replyToMsg==owner.reply&&SendMessagesHelper.sent.replyToTopMsg==owner.thread);SendMessagesHelper.ack();
  f=file();FlexyStickerSender.send(owner,f,doc,true,callback);p=SendMessagesHelper.sent;
  check(p.peer==7&&p.replyToMsg==null&&p.replyToTopMsg==null&&p.replyQuote==null&&p.monoForumPeer==0&&p.sendMessageChatArguments==null);SendMessagesHelper.ack();check(MediaDataController.favorites==1);
  owner.schedule=true;f=file();int before=SendMessagesHelper.sends;FlexyStickerSender.send(owner,f,doc,false,callback);
  check(SendMessagesHelper.sends==before&&f.isFile());AlertsCreator.cancelled.run();check(!f.exists()&&SendMessagesHelper.sends==before);
  f=file();FlexyStickerSender.send(owner,f,doc,false,callback);AlertsCreator.selected.run(false,123456,7);p=SendMessagesHelper.sent;
  check(!p.notify&&p.scheduleDate==123456&&p.scheduleRepeatPeriod==7&&p.replyToTopMsg==owner.thread);SendMessagesHelper.ack();check(!f.exists());
  f=file();FlexyStickerSender.send(owner,f,doc,false,callback);before=SendMessagesHelper.sends;UserConfig.instance.owner=8;AlertsCreator.selected.run(true,1,0);
  check(!f.exists()&&SendMessagesHelper.sends==before);UserConfig.instance.owner=7;
  owner.schedule=false;f=file();FlexyStickerSender.send(owner,f,doc,false,callback);NotificationCenter.getInstance(0).post(NotificationCenter.messageSendError,SendMessagesHelper.oldId);
  check(f.isFile()&&NotificationCenter.getInstance(0).size()==0);f.delete();
  f=file();FlexyStickerSender.send(owner,f,doc,false,callback);AndroidUtilities.timers.get(0).run();check(f.isFile()&&AndroidUtilities.timers.isEmpty()&&NotificationCenter.getInstance(0).size()==0);f.delete();
  owner.thread=null;f=file();before=SendMessagesHelper.sends;FlexyStickerSender.send(owner,f,doc,false,callback);check(!f.exists()&&SendMessagesHelper.sends==before);
  check(yes==4&&no==5);
 }
}'''
    probe(tmp_path, files, [JAVA/'app/flexygram/stickers/FlexyStickerSender.java'])


def test_saf_export_owns_files_closes_streams_and_reports_failures(tmp_path):
    files = platform()
    files['Probe.java'] = '''import java.io.*;import java.nio.file.*;import java.util.*;import java.util.concurrent.*;import app.flexygram.stickers.*;import android.content.*;import android.net.Uri;import org.telegram.messenger.*;import org.telegram.ui.ActionBar.BaseFragment;import org.telegram.ui.Components.BulletinFactory;
public class Probe{
 static byte[] payload=new byte[20000];
 static class Resolver extends ContentResolver{
  int mode,opens,closes;ByteArrayOutputStream bytes=new ByteArrayOutputStream();
  public OutputStream openOutputStream(Uri uri,String access)throws IOException{
   opens++;if(mode==4)return null;if(mode==7)throw new IOException("offline");
   if(access.equals("wt")){if(mode==1)return null;if(mode==2)throw new FileNotFoundException();if(mode==3)throw new IllegalArgumentException();}
   return new FilterOutputStream(bytes){public void write(byte[]b,int o,int n)throws IOException{if(mode==5)throw new IOException("full");out.write(b,o,n);}public void close()throws IOException{closes++;super.close();if(mode==6)throw new IOException("close failed");}};
  }
 }
 static File file()throws Exception{File f=File.createTempFile("sticker-export-",".webp");Files.write(f.toPath(),payload);return f;}
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void ui()throws Exception{long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(AndroidUtilities.ui.isEmpty()&&System.nanoTime()<end)Thread.sleep(1);Runnable r=AndroidUtilities.ui.poll();check(r!=null);r.run();}
 public static void main(String[]args)throws Exception{
  new Random(17).nextBytes(payload);BaseFragment owner=new BaseFragment();FlexyStickerExport exporter=new FlexyStickerExport();
  File f=file();check(exporter.begin(owner,f));check(owner.request==FlexyStickerExport.REQUEST_CODE&&owner.launched.action.equals(Intent.ACTION_CREATE_DOCUMENT)&&owner.launched.type.equals("image/webp")&&owner.launched.category.equals(Intent.CATEGORY_OPENABLE));
  check(!exporter.onActivityResult(owner,99,-1,null)&&f.isFile());check(exporter.onActivityResult(owner,owner.request,0,null)&&!f.exists());
  f=file();owner.throwLaunch=true;check(!exporter.begin(owner,f)&&f.isFile());owner.throwLaunch=false;check(exporter.begin(owner,f));exporter.cancel();check(!f.exists());
  check(exporter.onActivityResult(owner,owner.request,-1,new Intent("result").setData(new Uri())));
  f=file();check(exporter.begin(owner,f));Uri invalid=new Uri();invalid.scheme="file";int invalidErrors=BulletinFactory.errors;
  exporter.onActivityResult(owner,owner.request,-1,new Intent("result").setData(invalid));check(!f.exists()&&BulletinFactory.errors==invalidErrors+1);
  for(int mode=0;mode<8;mode++){
   Resolver resolver=new Resolver();resolver.mode=mode;ApplicationLoader.applicationContext.resolver=resolver;f=file();int good=BulletinFactory.successes,bad=BulletinFactory.errors;
   check(exporter.begin(owner,f));exporter.onActivityResult(owner,owner.request,-1,new Intent("result").setData(new Uri()));ui();check(!f.exists());
   if(mode<4){check(BulletinFactory.successes==good+1&&BulletinFactory.errors==bad&&resolver.closes==1&&Arrays.equals(resolver.bytes.toByteArray(),payload));check(resolver.opens==(mode==0?1:2));}
   else{check(BulletinFactory.successes==good&&BulletinFactory.errors==bad+1&&resolver.deletions==1);if(mode==5||mode==6)check(resolver.closes==1);}
  }
  f=file();check(exporter.begin(owner,f));owner.isFinished=true;exporter.cancel();check(!f.exists());owner.isFinished=false;
  var field=FlexyStickerExport.class.getDeclaredField("WORKER");field.setAccessible(true);ThreadPoolExecutor worker=(ThreadPoolExecutor)field.get(null);
  CountDownLatch started=new CountDownLatch(1),release=new CountDownLatch(1);worker.execute(()->{started.countDown();try{release.await();}catch(InterruptedException e){}});check(started.await(2,TimeUnit.SECONDS));worker.execute(()->{});worker.execute(()->{});
  f=file();check(exporter.begin(owner,f));int bad=BulletinFactory.errors;exporter.onActivityResult(owner,owner.request,-1,new Intent("result").setData(new Uri()));check(!f.exists()&&BulletinFactory.errors==bad+1);
  release.countDown();worker.shutdown();check(worker.awaitTermination(3,TimeUnit.SECONDS));
 }
}'''
    probe(tmp_path, files, [JAVA/'app/flexygram/stickers/FlexyStickerExport.java', JAVA/'app/flexygram/stickers/FlexyStickerSpec.java'])
    chat = (JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    assert 'flexyStickerExport.cancel();' in method(chat, 'public void onFragmentDestroy()')
    assert 'flexyStickerExport.onActivityResult(this, requestCode, resultCode, data)' in method(chat, 'public void onActivityResultFragment(')
