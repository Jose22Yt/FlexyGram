"""Execute production PhotoViewer controls; disk timing/GPU behavior are not simulated."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_video_preview_changes_do_not_persist_until_commit_and_compression_never_waits_for_disk(tmp_path):
    src=(JAVA/'org/telegram/ui/PhotoViewer.java').read_text()
    bodies='\n'.join(method(src,s) for s in ['private void chooseSpeed(', 'private void didChangedCompressionLevel('])
    probe(tmp_path,{'Probe.java':'''import java.util.*;
class Activity{static final int MODE_PRIVATE=0;}
class SharedPreferences{
 final Map<String,Object> values=new HashMap<>();int edits,writes;
 boolean contains(String k){return values.containsKey(k);}float getFloat(String k,float d){return (float)values.getOrDefault(k,d);}int getInt(String k,int d){return (int)values.getOrDefault(k,d);}
 Editor edit(){edits++;return new Editor();}class Editor{String key;Object value;boolean remove;
 Editor remove(String k){key=k;remove=true;return this;}Editor putFloat(String k,float v){key=k;value=v;return this;}Editor putInt(String k,int v){key=k;value=v;return this;}
 void apply(){writes++;if(remove)values.remove(key);else values.put(key,value);}boolean commit(){throw new AssertionError("Video control waited for disk");}}
}
class ApplicationLoader{static final Context applicationContext=new Context();static class Context{final SharedPreferences prefs=new SharedPreferences();SharedPreferences getSharedPreferences(String n,int m){return prefs;}}}
class MessagesController{static final SharedPreferences prefs=new SharedPreferences();static SharedPreferences getGlobalMainSettings(){return prefs;}}
public class Probe{
 static class Message{long getDialogId(){return 99;}int getId(){return 7;}}
 static class Player{float speed;int calls;void setPlaybackSpeed(float s){speed=s;calls++;}}
 static class Menu{int calls;void toggleSubMenu(){calls++;}}
 float currentVideoSpeed=1f;Message currentMessageObject=new Message();Player videoPlayer=new Player(),photoViewerWebView=new Player();Menu videoItem=new Menu();
 int compressionsCount=4,selectedCompression,updates,info,previews,icons;
 void setMenuItemIcon(boolean a,boolean b){icons++;}void updateWidthHeightBitrateForCompression(){updates++;}void updateVideoInfo(){info++;}void requestVideoPreview(int n){previews++;}
 BODIES
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();var prefs=ApplicationLoader.applicationContext.prefs;
 for(int i=0;i<1000;i++)p.chooseSpeed(1.1f+(i%10)*.1f,false,false);
 check(prefs.edits==0&&p.videoPlayer.calls==1000&&p.photoViewerWebView.calls==1000);
 float chosen=p.currentVideoSpeed;p.chooseSpeed(chosen,true,true);
 check(prefs.writes==1&&prefs.getFloat("speed99_7",0)==chosen&&p.videoPlayer.calls==1000&&p.videoItem.calls==1);
 p.chooseSpeed(chosen,true,false);check(prefs.writes==1);
 p.chooseSpeed(1f,true,false);check(prefs.writes==2&&!prefs.contains("speed99_7"));p.chooseSpeed(1f,true,false);check(prefs.writes==2);
 for(int i=0;i<10000;i++)p.didChangedCompressionLevel(false);
 check(MessagesController.prefs.writes==1&&p.updates==10000&&p.info==10000&&p.previews==0);
 p.selectedCompression=2;p.didChangedCompressionLevel(true);check(MessagesController.prefs.writes==2&&p.previews==1);
 }}'''.replace('BODIES',bodies)})
