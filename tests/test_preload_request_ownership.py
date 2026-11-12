"""Late storage results must not complete a new login's request for the same peer."""
from test_peer_preload50 import run


def test_same_owner_login_does_not_accept_or_complete_the_previous_session_result(tmp_path):
    run(tmp_path, '''Bundle b=new Bundle();b.user=900;int[] oldCalls={0},newCalls={0};
 check(ChatPeerPreloader.prepare(0,b,found->{oldCalls[0]++;}));
 MessagesStorage.getInstance(0).queue.fire();Runnable retired=AndroidUtilities.ui;
 UserConfig.getInstance(0).active=false;NotificationCenter.getInstance(0).logout();
 UserConfig.getInstance(0).active=true;
 check(ChatPeerPreloader.prepare(0,b,found->{check(found);newCalls[0]++;}));
 retired.run();
 check(oldCalls[0]==0&&newCalls[0]==0);
 check(MessagesController.getInstance(0).getUser(900)==null);
 check(NotificationCenter.getInstance(0).observers.size()==1);
 MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();
 check(newCalls[0]==1&&NotificationCenter.getInstance(0).observers.isEmpty());''')


def test_logout_cancels_queued_disk_work_even_if_the_same_owner_logs_in_again(tmp_path):
    run(tmp_path, '''Bundle b=new Bundle();b.user=901;int[] calls={0};
 check(ChatPeerPreloader.prepare(0,b,found->{calls[0]++;}));
 UserConfig.getInstance(0).active=false;NotificationCenter.getInstance(0).logout();
 UserConfig.getInstance(0).active=true;
 MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();
 check(MessagesStorage.reads==0&&calls[0]==0&&MessagesController.getInstance(0).getUser(901)==null);
 check(ChatPeerPreloader.prepare(0,b,found->{check(found);calls[0]++;}));
 MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();check(calls[0]==1);''')


def test_rejected_storage_queue_releases_request_and_allows_retry(tmp_path):
    from test_beta36_render_budget import peer_preload_hosts
    from test_render_work_reuse import probe, JAVA
    files = peer_preload_hosts()
    files['org/telegram/messenger/MessagesStorage.java'] = files['org/telegram/messenger/MessagesStorage.java'].replace(
        'public Runnable work;public boolean postRunnable(Runnable r){',
        'public boolean reject=true;public Runnable work;public boolean postRunnable(Runnable r){if(reject)return false;')
    files['Probe.java'] = """import android.os.Bundle;import app.flexygram.performance.ChatPeerPreloader;import org.telegram.messenger.*;
public class Probe{static void check(boolean ok){if(!ok)throw new AssertionError();}public static void main(String[]args){
 Bundle b=new Bundle();b.user=902;int[] failed={0},success={0};
 check(ChatPeerPreloader.prepare(0,b,found->{check(!found);failed[0]++;}));
 check(failed[0]==1&&MessagesStorage.reads==0&&NotificationCenter.getInstance(0).observers.isEmpty());
 MessagesStorage.getInstance(0).queue.reject=false;
 check(ChatPeerPreloader.prepare(0,b,found->{check(found);success[0]++;}));
 MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();
 check(success[0]==1&&NotificationCenter.getInstance(0).observers.isEmpty());
}}"""
    probe(tmp_path, files, [JAVA/'app/flexygram/performance/ChatPeerPreloader.java'])
