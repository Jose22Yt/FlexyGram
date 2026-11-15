"""Count actual production work with deterministic queues and compression doubles.

These regressions measure scans, accessibility publications and compression attempts;
they do not measure Android frame time or native WebP throughput.
"""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_folder_badge_batches_notifications_reads_latest_state_and_cancels(tmp_path):
    source = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    start = source.index('    private boolean folderUnreadBadgeUpdatePending;')
    end = source.index('\n    @Override', start)
    scheduler = source[start:end]
    event = method(source, 'if (id == NotificationCenter.dialogsUnreadCounterChanged ||')
    probe(tmp_path, {
        'app/flexygram/header/HeaderConfig.java': '''package app.flexygram.header;
public class HeaderConfig{public static boolean enabled=true;public static boolean counter(){return enabled;}}''',
        'Probe.java': '''import java.util.*;
public class Probe {
 static class NotificationCenter{static final int dialogsUnreadCounterChanged=1,dialogFiltersUpdated=2,dialogsNeedReload=3;}
 static class AndroidUtilities{
  static ArrayList<Runnable>queue=new ArrayList<>();static int posts;
  static void runOnUIThread(Runnable r){posts++;queue.add(r);}
  static void cancelRunOnUIThread(Runnable r){queue.removeIf(item->item==r);}
  static void fire(){ArrayList<Runnable>copy=new ArrayList<>(queue);queue.clear();for(Runnable r:copy)r.run();}
 }
 static class NekoConfig{static class Flag{boolean enabled;boolean Bool(){return enabled;}}static Flag unreadBadgeOnBackButton=new Flag();}
 static class Bar{int count,updates;void unreadBadgeSetCount(int v){count=v;updates++;}}
 Bar actionBar=new Bar();boolean paused,isFinished,signature;int scans,currentCount=1;
 boolean usesSignatureHeader(){return signature;}
 int getCurrentFolderUnreadMessageCount(){scans++;return currentCount;}
 void event(int id){EVENT}
 SCHEDULER
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();for(int i=0;i<1000;i++){p.currentCount=i;p.event(1+i%3);}
  check(p.scans==0&&AndroidUtilities.posts==1&&AndroidUtilities.queue.size()==1);
  AndroidUtilities.fire();check(p.scans==1&&p.actionBar.count==999&&p.actionBar.updates==1);
  p.event(1);p.cancelFolderUnreadBadgeUpdate();p.paused=true;AndroidUtilities.fire();
  for(int i=0;i<1000;i++)p.event(1);check(p.scans==1&&AndroidUtilities.queue.isEmpty());
  p.currentCount=42;p.paused=false;p.updateFolderUnreadBadge();check(p.scans==2&&p.actionBar.count==42);
  p.event(1);p.currentCount=43;p.updateFolderUnreadBadge();AndroidUtilities.fire();check(p.scans==3&&p.actionBar.count==43);
  p.event(1);p.isFinished=true;AndroidUtilities.fire();check(p.scans==3);p.isFinished=false;
  app.flexygram.header.HeaderConfig.enabled=false;p.event(2);AndroidUtilities.fire();check(p.scans==3&&p.actionBar.count==0);
  NekoConfig.unreadBadgeOnBackButton.enabled=true;p.event(1);AndroidUtilities.fire();check(p.scans==4&&p.actionBar.count==43);
  p.signature=true;p.event(1);AndroidUtilities.fire();check(p.scans==4&&p.actionBar.count==0);
  app.flexygram.header.HeaderConfig.enabled=true;p.event(1);AndroidUtilities.fire();check(p.scans==5&&p.actionBar.count==43);
  p.actionBar=null;p.event(1);check(AndroidUtilities.queue.isEmpty());
 }
}'''.replace('EVENT', event).replace('SCHEDULER', scheduler)
    })
    for signature in ('public void onPause()', 'public void onFragmentDestroy()'):
        assert 'cancelFolderUnreadBadgeUpdate();' in method(source, signature)
    resume = method(source, 'public void onResume()')
    assert 'updateFolderUnreadBadge();' in resume
    assert 'updateSignatureHeaderCounter();' not in resume


def test_tab_accessibility_reuses_unchanged_content_and_snapshots_mutable_text(tmp_path):
    source = (JAVA / 'org/telegram/ui/Components/glass/GlassTabView.java').read_text()
    start = source.index('    private String accessibilityTitle, accessibilityCount;')
    functions = source[start:source.rindex('\n}')]
    probe(tmp_path, {'Probe.java': '''
public class Probe {
 static class TextUtils{
  static boolean isEmpty(CharSequence s){return s==null||s.length()==0;}
  static boolean equals(CharSequence a,CharSequence b){if(a==b)return true;if(a==null||b==null||a.length()!=b.length())return false;
   for(int i=0;i<a.length();i++)if(a.charAt(i)!=b.charAt(i))return false;return true;}
 }
 static class Label{CharSequence text;CharSequence getText(){return text;}}
 Label textView=new Label(),counter=new Label();int publications;String description;
 void setContentDescription(CharSequence text){publications++;description=text.toString();}
 FUNCTIONS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();p.textView.text="Chats";p.counter.text="5";
  for(int i=0;i<10000;i++)p.updateContentDescription();check(p.publications==1&&p.description.equals("Chats, 5"));
  p.counter.text="6";p.updateContentDescription();check(p.publications==2&&p.description.equals("Chats, 6"));
  StringBuilder mutable=new StringBuilder("Contactos");p.textView.text=mutable;p.counter.text=null;p.updateContentDescription();
  mutable.append(" nuevos");p.updateContentDescription();check(p.publications==4&&p.description.equals("Contactos nuevos"));
  p.counter.text=new StringBuilder("2");p.updateContentDescription();
  ((StringBuilder)p.counter.text).append('3');p.updateContentDescription();check(p.description.equals("Contactos nuevos, 23"));
  p.counter.text="";p.updateContentDescription();check(p.description.equals("Contactos nuevos"));
 }
}'''.replace('FUNCTIONS', functions)})


def test_sticker_compression_cancellation_stops_retries_and_recycles(tmp_path):
    source = (JAVA / 'app/flexygram/stickers/FlexyStickerEncoder.java').read_text()
    functions = '\n'.join(method(source, signature) for signature in (
        'public static final class StickerBytes', 'public static StickerBytes encodeAndRecycle(',
        'private static void checkEncodingCancelled()'))
    probe(tmp_path, {'Probe.java': '''import java.io.*;
public class Probe {
 static class Build{static class VERSION{static int SDK_INT=30;}}
 static class FlexyStickerSpec{static final int MAX_BYTES=100;static boolean isWebp(byte[] b){return b.length>0&&b.length<=MAX_BYTES;}}
 static class Bitmap{
  enum CompressFormat{WEBP_LOSSLESS,WEBP_LOSSY,WEBP}
  int calls,recycles,interruptAt=-1,successAt=-1;boolean recycled;
  boolean isRecycled(){return recycled;}int getWidth(){return 512;}int getHeight(){return 256;}
  void recycle(){recycles++;recycled=true;}
  boolean compress(CompressFormat fmt,int quality,OutputStream out){calls++;
   if(calls==interruptAt)Thread.currentThread().interrupt();
   if(calls==successAt){try{out.write(1);}catch(IOException impossible){throw new AssertionError(impossible);}return true;}return false;}
 }
 FUNCTIONS
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void cancelled(Bitmap b,int expected)throws Exception{
  try{encodeAndRecycle(b);throw new AssertionError("cancelled encoder returned");}
  catch(InterruptedIOException expectedFailure){check(Thread.currentThread().isInterrupted());}
  finally{Thread.interrupted();}
  check(b.calls==expected&&b.recycles==1);
 }
 public static void main(String[]args)throws Exception{
  Bitmap b=new Bitmap();Thread.currentThread().interrupt();cancelled(b,0);
  b=new Bitmap();b.interruptAt=1;cancelled(b,1);
  b=new Bitmap();b.interruptAt=3;cancelled(b,3);
  b=new Bitmap();b.interruptAt=b.successAt=1;cancelled(b,1);
  Build.VERSION.SDK_INT=29;b=new Bitmap();b.interruptAt=1;cancelled(b,1);
  for(int api:new int[]{24,29,30,36}){Build.VERSION.SDK_INT=api;b=new Bitmap();b.successAt=2;
   StickerBytes data=encodeAndRecycle(b);check(b.calls==2&&b.recycles==1&&data.width==512&&data.height==256&&data.bytes.length==1);}
  Build.VERSION.SDK_INT=30;b=new Bitmap();try{encodeAndRecycle(b);throw new AssertionError();}catch(IOException expected){}
  check(b.calls==7&&b.recycles==1);
 }
}'''.replace('FUNCTIONS', functions)})
