"""Compact-player routing and policy regression checks; no packaged app or device claim."""
from pathlib import Path
import os,subprocess,shutil
import pytest
from test_render_work_reuse import JAVA,ROOT,probe
from test_composer_layout import method


def test_queue_window_is_bounded_and_contains_current_track_when_available(tmp_path):
    source=(JAVA/'app/exteraless/player/CompactPlayerQueue.java').read_text()
    body=method(source,'static int windowStart(')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 BODY
 public static void main(String[]args){for(int size=0;size<500;size++)for(int current=-1;current<size;current++){
 int start=windowStart(size,current,3);if(start<0||start>Math.max(0,size-3))throw new AssertionError();
 if(current>=0&&(current<start||current>=start+3))throw new AssertionError();
 }}}'''.replace('BODY',body)})


def test_close_buttons_stop_instead_of_turning_into_bubbles(tmp_path):
    for name in ['PlayerMiniView','PlayerBarView']:
        source=(JAVA/f'app/exteraless/player/{name}.java').read_text()
        click=method(source,'closeButton.setOnClickListener(v ->')
        body=click[click.index('{')+1:-1]
        probe(tmp_path,{'Probe.java':'''public class Probe{
 static class SignatureMusicPresentation{static boolean compact=true;static void setCompact(boolean v){compact=v;}}
 static class MediaController{static MediaController m=new MediaController();int stops;static MediaController getInstance(){return m;}void cleanupPlayer(boolean a,boolean b){stops++;}}
 Runnable onClose=()->MediaController.getInstance().cleanupPlayer(true,true);
 void close(){BODY}
 public static void main(String[]args){new Probe().close();if(SignatureMusicPresentation.compact||MediaController.m.stops!=1)throw new AssertionError();}
 }'''.replace('BODY',body)})


def test_music_routes_to_new_sheet_even_if_old_preference_was_disabled(tmp_path):
    source=(JAVA/'app/exteraless/player/Md3Player.java').read_text()
    enabled=method(source,'public static boolean enabled()')
    create=method(source,'public static BottomSheet create(')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class BuildConfig{static boolean CONNECTED_ALPHA=true;}static class AppearanceConfig{static boolean md3Player(){return false;}}
 static class Context{}static class Theme{interface ResourcesProvider{}}
 static class Message{boolean music=true;boolean isMusic(){return music;}}
 static class MediaController{static MediaController m=new MediaController();Message message=new Message();static MediaController getInstance(){return m;}Message getPlayingMessageObject(){return message;}}
 static class BottomSheet{}static class PlayerSheet extends BottomSheet{static PlayerSheet instance;PlayerSheet(Context c,Theme.ResourcesProvider p){}void dismissImmediately(){}}
 static class AudioPlayerAlert extends BottomSheet{AudioPlayerAlert(Context c,Theme.ResourcesProvider p){}}
 ENABLED
 static boolean handles(Message m){return enabled()&&m!=null&&m.isMusic();}
 CREATE
 public static void main(String[]args){if(!(create(new Context(),null)instanceof PlayerSheet))throw new AssertionError();
 MediaController.m.message.music=false;if(!(create(new Context(),null)instanceof AudioPlayerAlert))throw new AssertionError();}
 }'''.replace('ENABLED',enabled).replace('CREATE',create)})


def test_music_widget_api_contract():
    if not shutil.which('javac') or not Path('/tmp/flexy-performance-libs/core.jar').is_file():pytest.skip('JDK and AndroidX Core API jar required')
    result=subprocess.run(['python',str(ROOT/'tools/connected_alpha/check_compact_player_types.py')],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr


def test_full_player_progress_does_not_rebuild_queue_or_extract_artwork_colors():
    source=(JAVA/'app/exteraless/player/PlayerSheet.java').read_text()
    assert 'compactQueue.refresh' not in method(source,'private void updateProgress(')
    assert 'if (!BuildConfig.CONNECTED_ALPHA) cover.setListener' in source
    assert 'if (!BuildConfig.CONNECTED_ALPHA) o.add(R.drawable.msg_filled_data_music' in source
    bubble=(JAVA/'app/exteraless/player/SignatureMusicBubble.java').read_text()
    assert 'private void openPlayer()' in bubble and 'Md3Player.open(fragment,null)' in bubble
    assert 'owner.clear()' in bubble


def test_queue_identity_never_confuses_accounts_dialogs_or_local_zero_ids(tmp_path):
    source=(JAVA/'app/exteraless/player/CompactPlayerQueue.java').read_text()
    body=method(source,'static boolean sameMessage(')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class MessageObject{int currentAccount,id=7;long dialog=12;int getId(){return id;}long getDialogId(){return dialog;}}
 BODY
 public static void main(String[]args){MessageObject a=new MessageObject(),b=new MessageObject();
 if(!sameMessage(a,b)||sameMessage(null,b))throw new AssertionError();b.currentAccount=1;if(sameMessage(a,b))throw new AssertionError();
 b.currentAccount=0;b.dialog=13;if(sameMessage(a,b))throw new AssertionError();b.dialog=12;a.id=b.id=0;
 if(sameMessage(a,b)||!sameMessage(a,a))throw new AssertionError();}
 }'''.replace('BODY',body)})
