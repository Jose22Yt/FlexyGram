"""Session queue and render work regressions. No APK or device FPS claims."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, ROOT, probe

MESSAGE = '''package org.telegram.messenger;public class MessageObject {
 public int currentAccount,id;public long dialog;public boolean scheduled,music=true,once,mediaExists=true;public float audioProgress=.37f;public int audioProgressSec=37,resets;
 public MessageObject(int account,long dialog,int id){currentAccount=account;this.dialog=dialog;this.id=id;}
 public int getId(){return id;}public long getDialogId(){return dialog;}public boolean isMusic(){return music;}
 public boolean isVoiceOnce(){return once;}public boolean isRoundOnce(){return false;}
 public void resetPlayingProgress(){resets++;audioProgress=0;audioProgressSec=0;}}
'''


def test_queue_model_identity_growth_limits_and_unicode_search(tmp_path):
    probe(tmp_path, {
        'org/telegram/messenger/MessageObject.java': MESSAGE,
        'Probe.java': '''import java.util.*;import org.telegram.messenger.MessageObject;import app.exteraless.player.MusicQueueOrder;
public class Probe {
 static MessageObject m(int a,long d,int i){return new MessageObject(a,d,i);}static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
 MessageObject playing=m(0,9000000001L,7),sameIdOtherDialog=m(0,9000000002L,7),otherAccount=m(1,9000000001L,7);
 check(!MusicQueueOrder.same(playing,sameIdOtherDialog)&&!MusicQueueOrder.same(playing,otherAccount));
 check(MusicQueueOrder.same(playing,m(0,9000000001L,7)));
 MessageObject zero=m(0,1,0);check(MusicQueueOrder.same(zero,zero)&&!MusicQueueOrder.same(zero,m(0,1,0)));
 ArrayList<MessageObject> q=new ArrayList<>(List.of(playing));
 check(!MusicQueueOrder.enqueue(q,playing,otherAccount,true)&&q.size()==1);
 check(MusicQueueOrder.enqueue(q,playing,sameIdOtherDialog,true)&&q.get(1)==sameIdOtherDialog);
 check(!MusicQueueOrder.remove(q,playing,playing));
 check(MusicQueueOrder.enqueue(q,playing,sameIdOtherDialog,false)&&q.size()==2);
 for(int i=2;i<MusicQueueOrder.MAX_TRACKS;i++)q.add(m(0,2,i));
 check(!MusicQueueOrder.enqueue(q,playing,m(0,3,8),true));
 check(MusicQueueOrder.enqueue(q,playing,sameIdOtherDialog,true));
 check(MusicQueueOrder.remove(q,playing,sameIdOtherDialog)&&q.size()==MusicQueueOrder.MAX_TRACKS-1);
 String text=MusicQueueOrder.normalize("CANCIÓN · Éminem · Archivo.MP3");
 check(MusicQueueOrder.matches(text,MusicQueueOrder.normalize("eminem cancion")));
 check(MusicQueueOrder.matches(text,new String[]{"archivo","mp3"}));check(!MusicQueueOrder.matches(text,"missing"));
 check(MusicQueueOrder.normalize(null).isEmpty());
 for(int size=1;size<40;size++){
 ArrayList<MessageObject> source=new ArrayList<>();for(int i=0;i<size;i++)source.add(m(0,1,i+1));
 for(boolean forward:new boolean[]{false,true}){
 var audible=MusicQueueOrder.audible(source,forward);check(MusicQueueOrder.audible(audible,forward).equals(source));
 audible.clear();check(source.size()==size);
 }}
 }}'''
    }, [JAVA/'app/exteraless/player/MusicQueueOrder.java'])


def test_native_queue_edits_preserve_playback_shuffle_and_reject_stale_drag(tmp_path):
    source = (JAVA/'org/telegram/messenger/MediaController.java').read_text()
    signatures = ['public java.util.List<MessageObject> getMusicPlaybackOrder(',
                  'public ArrayList<MessageObject> getMusicQueueSnapshot(',
                  'public boolean enqueueMusic(', 'public boolean removeMusicFromQueue(',
                  'public boolean moveMusicInQueue(', 'public boolean reorderMusicQueue(',
                  'private boolean applyMusicQueue(', 'private boolean traversePlaylist(',
                  'private void playNextMessageWithoutOrder(']
    methods = '\n'.join(method(source, s) for s in signatures)
    probe(tmp_path, {
        'org/telegram/messenger/MessageObject.java': MESSAGE,
        'Probe.java': '''import java.util.*;import org.telegram.messenger.MessageObject;
public class Probe {
 static class SharedConfig{static boolean shuffleMusic,playOrderReversed;static int repeatMode;}
 static class UserConfig{static int selectedAccount;}static class ConnectionsManager{static final int ConnectionStateWaitingForNetwork=1;static ConnectionsManager getInstance(int a){return new ConnectionsManager();}int getConnectionState(){return 0;}}
 static class AudioPlayerAlert{static final int PLAY_ONCE=3;}
 static class NotificationCenter{static final int moreMusicDidLoad=1;static int events;static NotificationCenter getInstance(int a){return new NotificationCenter();}void postNotificationName(int id,Object...args){events++;}}
 MessageObject playingMessageObject;ArrayList<MessageObject>playlist=new ArrayList<>(),shuffledPlaylist=new ArrayList<>();Map<Integer,MessageObject>playlistMap=new HashMap<>();
 int currentPlaylistNum,playlistClassGuid=17,cleanup,stops;boolean editedMusicQueue,forceLoopCurrentPlaylist,playMusicAgain,loadingPlaylist=true;
 boolean[]playlistEndReached=new boolean[2];Object currentSavedMusicList=new Object(),savedMusicPlaylistState=new Object(),playlistGlobalSearchParams=new Object();
 boolean playMessage(MessageObject item){playingMessageObject=item;return true;}
 void cleanupPlayer(boolean a,boolean b){cleanup++;}void stopPlaybackOnTrackEnd(){stops++;}
 boolean setPlaylist(ArrayList<MessageObject> items,MessageObject item,long d,boolean load,Object params){playlist.clear();playlist.addAll(items);shuffledPlaylist.clear();shuffledPlaylist.addAll(items);playingMessageObject=item;return true;}
 METHODS
 static MessageObject m(int id){return new MessageObject(0,9000000001L,id);}static void check(boolean b){if(!b)throw new AssertionError();}
 static Probe init(boolean forward,boolean shuffle){SharedConfig.playOrderReversed=forward;SharedConfig.shuffleMusic=shuffle;SharedConfig.repeatMode=0;
 Probe p=new Probe();var a=m(1);var b=m(2);var c=m(3);p.playingMessageObject=b;
 p.playlist.addAll(forward?List.of(a,b,c):List.of(c,b,a));p.shuffledPlaylist.addAll(p.playlist);p.currentPlaylistNum=1;return p;}
 public static void main(String[]args){
 Probe unchanged=init(false,false);Object saved=unchanged.currentSavedMusicList;var original=unchanged.getMusicQueueSnapshot();
 check(unchanged.reorderMusicQueue(new ArrayList<>(original),original)&&!unchanged.editedMusicQueue&&unchanged.currentSavedMusicList==saved);
 for(boolean forward:new boolean[]{false,true})for(boolean shuffle:new boolean[]{false,true}){
 Probe p=init(forward,shuffle);MessageObject playing=p.playingMessageObject,next=m(4),tail=m(5);
 check(p.enqueueMusic(next,true));check(p.playingMessageObject==playing&&playing.audioProgress==.37f&&playing.resets==0&&p.cleanup==0);
 check(p.editedMusicQueue&&p.currentSavedMusicList==null&&p.savedMusicPlaylistState==null&&p.playlistGlobalSearchParams==null&&p.playlistClassGuid==0&&!p.loadingPlaylist&&!p.forceLoopCurrentPlaylist);
 check(SharedConfig.shuffleMusic==shuffle&&SharedConfig.playOrderReversed==forward);
 check(p.getMusicQueueSnapshot().get(2)==next);check(p.enqueueMusic(tail,false));check(p.getMusicQueueSnapshot().get(4)==tail);
 check(!p.removeMusicFromQueue(playing));check(p.removeMusicFromQueue(tail));
 ArrayList<MessageObject> expected=p.getMusicQueueSnapshot(),desired=new ArrayList<>(expected);Collections.swap(desired,2,3);
 check(p.reorderMusicQueue(desired,expected));check(p.playingMessageObject==playing&&playing.audioProgress==.37f);
 check(!p.reorderMusicQueue(expected,expected));
 var duplicate=new ArrayList<>(desired);duplicate.set(0,duplicate.get(1));check(!p.reorderMusicQueue(duplicate,desired));
 check(p.enqueueMusic(next,true));p.playNextMessageWithoutOrder(false);check(p.playingMessageObject==next);
 MessageObject foreign=new MessageObject(1,9000000001L,9);check(!p.enqueueMusic(foreign,true));
 next.scheduled=true;check(!p.enqueueMusic(next,true));next.scheduled=false;
 }
 Probe p=new Probe();p.currentSavedMusicList=null;check(p.enqueueMusic(m(9),false));check(p.editedMusicQueue&&!p.forceLoopCurrentPlaylist&&p.playingMessageObject.id==9);
 p.playNextMessageWithoutOrder(true);check(p.stops==1);
 }}'''.replace('METHODS', methods)
    }, [JAVA/'app/exteraless/player/MusicQueueOrder.java'])
    assert '!editedMusicQueue && playingMessageObject' in source
    assert '!editedMusicQueue && guid == playlistClassGuid' in source
    assert 'if (editedMusicQueue) return;' in method(source, 'public void loadMoreMusic()')


def test_luminous_ring_reuses_shaders_and_never_schedules_a_frame(tmp_path):
    probe(tmp_path, {
        'android/graphics/Shader.java': '''package android.graphics;public class Shader {public enum TileMode{CLAMP}public static int instances;public Shader(){instances++;}public void setLocalMatrix(Matrix m){}}''',
        'android/graphics/Matrix.java': 'package android.graphics;public class Matrix{public void setRotate(float d,float x,float y){if(!Float.isFinite(d))throw new AssertionError();}public void setTranslate(float x,float y){if(!Float.isFinite(x+y))throw new AssertionError();}}',
        'android/graphics/SweepGradient.java': 'package android.graphics;public class SweepGradient extends Shader{public SweepGradient(float x,float y,int[]c,float[]p){}}',
        'android/graphics/RadialGradient.java': 'package android.graphics;public class RadialGradient extends Shader{public RadialGradient(float x,float y,float r,int[]c,float[]p,TileMode m){if(r<=0)throw new AssertionError();}}',
        'android/graphics/Paint.java': '''package android.graphics;public class Paint{public static final int ANTI_ALIAS_FLAG=1;public enum Style{STROKE}public enum Cap{ROUND}public Paint(int f){}public void setStyle(Style s){}public void setStrokeCap(Cap c){}public void setStrokeWidth(float f){}public void setColor(int c){}public void setShader(Shader s){}public void setAlpha(int a){if(a<0||a>255)throw new AssertionError();}}''',
        'android/graphics/Canvas.java': '''package android.graphics;public class Canvas{public int arcs,glows;public void drawArc(float l,float t,float r,float b,float start,float sweep,boolean center,Paint p){if(!Float.isFinite(sweep)||sweep<0||sweep>360)throw new AssertionError();arcs++;}public void drawCircle(float x,float y,float r,Paint p){glows++;}}''',
        'android/graphics/Color.java': '''package android.graphics;public class Color{public static final int WHITE=-1;public static int red(int c){return c>>>16&255;}public static int green(int c){return c>>>8&255;}public static int blue(int c){return c&255;}public static int rgb(int r,int g,int b){return 0xff000000|r<<16|g<<8|b;}}''',
        'org/telegram/messenger/AndroidUtilities.java': 'package org.telegram.messenger;public class AndroidUtilities{public static float density=1;public static float dpf2(float f){return density*f;}}',
        'app/exteraless/player/Probe.java': '''package app.exteraless.player;import android.graphics.*;import org.telegram.messenger.AndroidUtilities;
public class Probe {public static void main(String[]args){LuminousProgressRing ring=new LuminousProgressRing();Canvas c=new Canvas();ring.setColors(0xff24624d,0xffdddddd);
 for(int i=0;i<10000;i++)ring.draw(c,280,280,(i%1000)/1000f,1);
 if(Shader.instances!=2)throw new AssertionError("gradient allocated per frame");
 int before=c.arcs;ring.draw(c,280,280,.5f,0);if(c.arcs!=before)throw new AssertionError();
 ring.draw(c,280,280,Float.NaN,1);ring.draw(c,280,280,Float.POSITIVE_INFINITY,1);
 ring.setColors(0xff24624d,0xffdddddd);ring.draw(c,280,280,.5f,1);if(Shader.instances!=2)throw new AssertionError();
 ring.setColors(0xff772244,0xffdddddd);ring.draw(c,280,280,.5f,1);if(Shader.instances!=4)throw new AssertionError();
 AndroidUtilities.density=2;ring.draw(c,280,280,.5f,1);if(Shader.instances!=6)throw new AssertionError();
 }}''',
        'Probe.java': 'public class Probe{public static void main(String[]a){app.exteraless.player.Probe.main(a);}}'
    }, [JAVA/'app/exteraless/player/LuminousProgressRing.java'])
    renderer = (JAVA/'app/exteraless/player/LuminousProgressRing.java').read_text()
    assert all(word not in renderer for word in ['postDelayed(', 'postInvalidate', 'new Bitmap', 'BlurMaskFilter', 'RenderEffect'])


def test_player_wiring_search_drag_and_localization_keep_native_owners():
    import re
    import xml.etree.ElementTree as ET
    queue = (JAVA/'app/exteraless/player/PlayerQueueSheet.java').read_text()
    assert 'searchIndex.add' not in method(queue, 'private void applySearch(')
    assert 'getMusicQueueSnapshot' not in method(queue, 'private void applySearch(')
    notification = method(queue, 'public void didReceivedNotification(')
    assert 'messagePlayingProgressDidChanged' not in notification
    moving = method(queue, 'public boolean onMove(')
    assert 'MediaController' in moving  # only the read of the current message
    assert 'reorderMusicQueue' not in moving and 'moveMusicInQueue' not in moving
    assert 'reorderMusicQueue' in method(queue, 'public void clearView(')
    assert 'search.length()!=0' in method(queue, 'public int getMovementFlags(')
    assert 'cancelRunOnUIThread(searchTask)' in method(queue, 'public void dismiss()')
    assert 'super(context, true, resourcesProvider)' in queue  # allow the search IME
    orbit = (JAVA/'app/exteraless/player/OrbitArtwork.java').read_text()
    assert 'luminousRing.draw' in method(orbit, 'protected void dispatchDraw(')
    assert 'postDelayed' not in orbit and 'new LuminousProgressRing' in orbit
    mini = (JAVA/'app/exteraless/player/RingPlayButton.java').read_text()
    draw = method(mini, 'protected void onDraw(')
    assert 'waveEnabled && visible' in draw and 'visible && amplitude > 0f && playing' in draw
    for name in ['PlayerMiniView', 'PlayerBarView']:
        assert 'setWaveEnabled(true)' in (JAVA/f'app/exteraless/player/{name}.java').read_text()
    resources = ROOT/'TMessagesProj/src/main/res'
    keys = None
    for locale in ['values', 'values-es', 'values-ru']:
        found = {e.get('name') for e in ET.parse(resources/locale/'flexygram_music_queue.xml').getroot()}
        if keys is None: keys = found
        assert found == keys
    available_drawables = {p.stem for p in resources.glob('drawable*/*')}
    for filename in ['MusicQueueActions', 'PlayerQueueSheet', 'OrbitPlayerLayout']:
        source = (JAVA/f'app/exteraless/player/{filename}.java').read_text()
        assert not (set(re.findall(r'R\.drawable\.(\w+)', source)) - available_drawables)
