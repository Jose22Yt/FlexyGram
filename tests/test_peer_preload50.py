"""Actual cold-peer preload correctness and storage work counts, not physical FPS."""
from test_beta36_render_budget import peer_preload_hosts
from test_render_work_reuse import JAVA, probe

PRELOADER=JAVA/'app/flexygram/performance/ChatPeerPreloader.java'


def run(tmp_path,body):
    files=peer_preload_hosts()
    files['Probe.java']='''import android.os.Bundle;import app.flexygram.performance.ChatPeerPreloader;import org.telegram.messenger.*;import org.telegram.tgnet.TLRPC;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args)throws Exception{BODY}}'''.replace('BODY',body)
    probe(tmp_path,files,[PRELOADER])


def test_repeated_taps_share_one_storage_read_and_all_callbacks_finish_on_ui(tmp_path):
    run(tmp_path,'''Bundle b=new Bundle();b.user=42;int[] calls={0};
 for(int i=0;i<20;i++)check(ChatPeerPreloader.prepare(0,b,found->{check(found&&!MessagesStorage.onStorage);calls[0]++;}));
 check(MessagesStorage.reads==0&&calls[0]==0);MessagesStorage.getInstance(0).queue.fire();
 check(MessagesStorage.reads==1&&calls[0]==0);AndroidUtilities.ui.run();check(calls[0]==20);
 check(!ChatPeerPreloader.prepare(0,b,found->{throw new AssertionError();}));''')


def test_logout_or_owner_replacement_discards_queued_work_and_late_cache_results(tmp_path):
    run(tmp_path,'''Bundle b=new Bundle();b.user=100;int[] calls={0};
 check(ChatPeerPreloader.prepare(0,b,found->{check(!found);calls[0]++;}));
 UserConfig.getInstance(0).owner=2000;MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();
 check(MessagesStorage.reads==0&&MessagesController.getInstance(0).getUser(100)==null&&calls[0]==1);
 b.user=101;check(ChatPeerPreloader.prepare(0,b,found->{check(!found);calls[0]++;}));MessagesStorage.getInstance(0).queue.fire();
 UserConfig.getInstance(0).active=false;AndroidUtilities.ui.run();check(MessagesController.getInstance(0).getUser(101)==null&&calls[0]==2);
 UserConfig.getInstance(0).active=true;check(ChatPeerPreloader.prepare(0,b,found->{check(found);calls[0]++;}));
 MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();check(calls[0]==3);''')


def test_newer_live_user_and_chat_data_win_over_storage_snapshot(tmp_path):
    run(tmp_path,'''Bundle b=new Bundle();b.user=300;int[] calls={0};
 check(ChatPeerPreloader.prepare(0,b,found->{check(found);calls[0]++;}));MessagesStorage.getInstance(0).queue.fire();
 TLRPC.User fresh=new TLRPC.User();fresh.id=300;MessagesController.getInstance(0).putUser(fresh,false);
 AndroidUtilities.ui.run();check(MessagesController.getInstance(0).getUser(300)==fresh&&calls[0]==1);
 b.user=0;b.chat=400;check(ChatPeerPreloader.prepare(0,b,found->{check(found);calls[0]++;}));MessagesStorage.getInstance(0).queue.fire();
 TLRPC.Chat chat=new TLRPC.Chat();chat.id=400;MessagesController.getInstance(0).putChat(chat,false);
 AndroidUtilities.ui.run();check(MessagesController.getInstance(0).getChat(400)==chat&&calls[0]==2);''')


def test_controller_recreation_with_same_owner_cannot_inject_into_retired_instance(tmp_path):
    run(tmp_path,'''Bundle b=new Bundle();b.user=500;int[] calls={0};MessagesController retired=MessagesController.getInstance(0);
 check(ChatPeerPreloader.prepare(0,b,found->{check(!found);calls[0]++;}));MessagesStorage.getInstance(0).queue.fire();
 java.lang.reflect.Field field=MessagesController.class.getDeclaredField("instances");field.setAccessible(true);
 MessagesController[] controllers=(MessagesController[])field.get(null);controllers[0]=new MessagesController();
 AndroidUtilities.ui.run();check(retired.getUser(500)==null&&controllers[0].getUser(500)==null&&calls[0]==1);''')


def test_failed_read_can_retry_from_callback_and_one_bad_listener_does_not_block_others(tmp_path):
    run(tmp_path,'''Bundle b=new Bundle();b.user=600;int[] failed={0},success={0};MessagesStorage.fail=true;
 check(ChatPeerPreloader.prepare(0,b,found->{check(!found);failed[0]++;MessagesStorage.fail=false;
 check(ChatPeerPreloader.prepare(0,b,next->{check(next);success[0]++;}));throw new IllegalStateException("listener failure");}));
 check(ChatPeerPreloader.prepare(0,b,found->{check(!found);failed[0]++;}));
 MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();check(failed[0]==2);
 MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();check(success[0]==1);''')


def test_logout_releases_pending_callbacks_even_if_storage_queue_stops(tmp_path):
    run(tmp_path,'''Bundle b=new Bundle();b.user=700;int[] calls={0};
 check(ChatPeerPreloader.prepare(0,b,found->{calls[0]++;}));check(NotificationCenter.getInstance(0).observers.size()==1);
 UserConfig.getInstance(0).active=false;NotificationCenter.getInstance(0).logout();check(NotificationCenter.getInstance(0).observers.isEmpty());
 java.lang.reflect.Field field=ChatPeerPreloader.class.getDeclaredField("pending");field.setAccessible(true);check(((java.util.Map<?,?>)field.get(null)).isEmpty());
 MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();check(calls[0]==0);
 UserConfig.getInstance(0).active=true;check(ChatPeerPreloader.prepare(0,b,found->{check(found);calls[0]++;}));
 MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();check(calls[0]==1&&NotificationCenter.getInstance(0).observers.isEmpty());''')


def test_inactive_account_fails_without_requesting_synchronous_chat_open_fallback(tmp_path):
    run(tmp_path,'''Bundle b=new Bundle();b.user=800;UserConfig.getInstance(0).active=false;int[] calls={0};
 check(ChatPeerPreloader.prepare(0,b,found->{check(!found);calls[0]++;}));
 check(MessagesStorage.reads==0&&MessagesStorage.getInstance(0).queue.work==null);AndroidUtilities.ui.run();
 check(calls[0]==1&&NotificationCenter.getInstance(0).observers.isEmpty());''')
