/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

import android.os.Bundle;
import android.view.View;
import android.widget.FrameLayout;
import java.lang.ref.WeakReference;
import java.util.Calendar;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.ArrayList;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.DialogObject;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.SharedConfig;
import org.telegram.messenger.UserConfig;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ChatActivity;
import org.telegram.ui.LaunchActivity;
import tw.nekomimi.nekogram.helpers.PasscodeHelper;

/** UI-thread coordinator. No Activity is retained while paused; no background wakeups. */
public final class CameraPopRuntime implements NotificationCenter.NotificationCenterDelegate {
    private static volatile int foregroundIslandAccount=-1;
    private static final CameraPopRuntime INSTANCE=new CameraPopRuntime();
    private static final int[] EVENTS={NotificationCenter.didReceiveNewMessages,NotificationCenter.messagesRead,NotificationCenter.messagesDeleted,
            NotificationCenter.dialogsNeedReload,NotificationCenter.dialogsUnreadCounterChanged,
            NotificationCenter.notificationsSettingsUpdated,NotificationCenter.openedChatChanged,NotificationCenter.appDidLogout};
    private static final class AccountState {
        final long owner;
        CameraPopConfig config;
        final CameraPopState state=new CameraPopState();
        final CameraPopInbox inbox=new CameraPopInbox();
        final Set<Long> candidates=new HashSet<>();
        long boundRevision=-1;
        int indexedSize=-1;
        AccountState(int account) {owner=UserConfig.getInstance(account).getClientUserId();config=new CameraPopConfig(account);config.load(state);}
    }
    private final Map<Integer,AccountState> accounts=new HashMap<>();
    private final Set<Integer> dirtyAccounts=new HashSet<>();
    private final Set<Long> entryPending=new HashSet<>();
    private final Set<Long> livePending=new HashSet<>();
    private final Map<Long,Integer> liveRetries=new HashMap<>();
    private int sessionAccount=-1;
    private long quietClockMinute=Long.MIN_VALUE;
    private int quietMinute;
    private WeakReference<LaunchActivity> host=new WeakReference<>(null);
    private int observing=-1;
    private CameraPopCapsule capsule;
    private long visibleDialog;
    private boolean demo, globals, drainScheduled,reconcileScheduled;
    private ArrayList<TLRPC.Dialog> indexing;
    private int indexPosition,indexAccount=-1;
    private final Runnable indexNext=this::indexNext;
    private final Runnable drain=()->{drainScheduled=false;drain();};
    private final Runnable expire=this::expire;
    private final Runnable deadline=this::deadline;
    private final Runnable reconcile=()->{reconcileScheduled=false;reconcile();};
    private final Runnable persist=this::flushSaves;
    private CameraPopRuntime() {}
    private AccountState account(int account) {
        AccountState value=accounts.get(account);
        if(value==null || value.owner!=UserConfig.getInstance(account).getClientUserId()) {
            value=new AccountState(account);accounts.put(account,value);
        }
        return value;
    }

    /** Native message events, independent of the system-notification pipeline. UI thread only. */
    public static void incoming(int account,MessageObject message) {
        if(!CameraPopConfig.enabled(account) || message==null || message.messageOwner==null || message.getId()<=0
                || message.isOutOwner() || message.messageOwner.from_scheduled
                || message.isReactionPush || message.isStoryReactionPush || message.isOauthPush
                || !message.messageOwner.unread || message.isImportedForward()
                || (message.messageOwner.action!=null && !(message.messageOwner.action instanceof TLRPC.TL_messageActionEmpty))) return;
        // Capture primitives only; never retain MessageObject or private message content.
        long dialog=message.getDialogId(); int id=message.getId();
        if(!CameraPopConfig.interested(account,dialog))return;
        long topic=MessageObject.getTopicId(account,message.messageOwner,MessagesController.getInstance(account).isForum(message));
        INSTANCE.accept(account,dialog,id,topic);
    }
    private void accept(int id,long dialog,int message,long topic) {
        if(!UserConfig.getInstance(id).isClientActivated() || !CameraPopConfig.enabled(id)) return;
        AccountState a=account(id); CameraPopConfig c=a.config;
        if(!c.enabled || !c.matches(dialog)) return;
        a.candidates.add(dialog);
        if(!a.state.incoming(dialog,message,topic,System.currentTimeMillis(),c.interval())) return;
        saveSoon(id);
        // Queue even while focus/counters are settling; revalidate when actually showing.
        if(id==observing && c.immediate) {
            if(demo)hide();
            livePending.add(dialog);
            liveRetries.put(dialog,3);
            if(capsule==null) {a.state.enqueue(dialog);requestDrain(320);}
        }
        if(capsule!=null && !demo){a.inbox.update(dialog,Math.max(0,unread(dialog)),true);requestReconcile();}
        schedule();
    }

    public static void resume(LaunchActivity activity) {
        INSTANCE.host=new WeakReference<>(activity);
        INSTANCE.sessionAccount=-1;INSTANCE.entryPending.clear();
        // Post to the next frame; optional reminders never delay activity initialization.
        AndroidUtilities.cancelRunOnUIThread(INSTANCE.reconcile);
        INSTANCE.reconcileScheduled=true;
        activity.getWindow().getDecorView().postOnAnimation(INSTANCE.reconcile);
    }
    public static void accountChanged(LaunchActivity activity) {
        if(INSTANCE.host.get()==activity) INSTANCE.reconcile();
    }
    public static void conceal() { INSTANCE.hide(); }
    public static void windowFocusChanged(LaunchActivity activity,boolean focused) {
        if(INSTANCE.host.get()!=activity)return;
        if(focused)INSTANCE.reconcile();else {foregroundIslandAccount=-1;INSTANCE.hide();INSTANCE.refreshAndroid();}
    }
    public static void pause(LaunchActivity activity) {
        if(INSTANCE.host.get()!=activity) return;
        activity.getWindow().getDecorView().removeCallbacks(INSTANCE.reconcile);
        INSTANCE.stop();INSTANCE.host.clear();INSTANCE.refreshAndroid();
    }
    public static void configurationChanged(int id) {
        AndroidUtilities.cancelRunOnUIThread(INSTANCE.indexNext);INSTANCE.indexing=null;INSTANCE.indexAccount=-1;
        INSTANCE.dirtyAccounts.remove(id);
        if(INSTANCE.dirtyAccounts.isEmpty())AndroidUtilities.cancelRunOnUIThread(INSTANCE.persist);
        AccountState a=INSTANCE.account(id);long previousInterval=a.config.interval();
        Set<Long> oldSelected=a.config.selected;a.config=new CameraPopConfig(id);
        if(INSTANCE.observing==id) {
            INSTANCE.entryPending.retainAll(a.config.selected);
            INSTANCE.livePending.retainAll(a.config.selected);
            INSTANCE.liveRetries.keySet().retainAll(a.config.selected);
            for(long dialog:a.config.selected)if(!oldSelected.contains(dialog))INSTANCE.entryPending.add(dialog);
        }
        if(!a.config.allChats) {a.state.retain(a.config.selected);a.candidates.retainAll(a.config.selected);a.candidates.addAll(a.config.selected);}
        if(INSTANCE.observing==id)INSTANCE.entryPending.addAll(a.candidates);
        a.indexedSize=-1;a.inbox.clear();a.boundRevision=-1;a.state.clearQueue();
        if(!a.config.enabled) {a.state.clear();a.config.clearPending();}
        else {
            if(previousInterval!=a.config.interval()) {
                for(CameraPopState.Pending p:a.state.pending()) a.state.defer(p.dialog,System.currentTimeMillis()+a.config.interval());
            }
            // Selecting a chat also enables reminders for messages already pending.
            for(long dialog:a.config.selected) {
                TLRPC.Dialog value=MessagesController.getInstance(id).dialogs_dict.get(dialog);
                if(a.state.get(dialog)==null && value!=null && value.unread_count>0)
                    a.state.seed(dialog,value.top_message,System.currentTimeMillis(),a.config.interval());
            }
            a.config.save(a.state);
        }
        INSTANCE.hide();INSTANCE.reconcile();INSTANCE.refreshAndroid();
    }
    public static void demonstrate() {
        LaunchActivity activity=INSTANCE.host.get();
        if(activity==null || !INSTANCE.safeWindow(activity)) return;
        INSTANCE.hide();INSTANCE.demo=true;INSTANCE.visibleDialog=0;
        if(!INSTANCE.createCapsule(activity)) return;
        ArrayList<CameraPopInbox.Row> sample=new ArrayList<>();sample.add(new CameraPopInbox.Row(0,2));sample.add(new CameraPopInbox.Row(-1,3));
        INSTANCE.capsule.bindRows(UserConfig.selectedAccount,false,sample,INSTANCE::openChat,INSTANCE::expansionChanged);
        INSTANCE.startCapsule();
    }

    private boolean safeWindow(LaunchActivity activity) {
        return !activity.isFinishing() && !activity.isDestroyed() && activity.hasWindowFocus()
                && !SharedConfig.appLocked && !SharedConfig.isWaitingForPasscodeEnter
                && !AndroidUtilities.needShowPasscode() && !PasscodeHelper.isAccountHidden(UserConfig.selectedAccount)
                && (android.os.Build.VERSION.SDK_INT<24 || !activity.isInPictureInPictureMode());
    }
    private boolean allowed(AccountState a,long dialog) {
        LaunchActivity activity=host.get();
        if(activity==null || !safeWindow(activity) || !a.config.enabled || !a.config.matches(dialog)) return false;
        BaseFragment top=LaunchActivity.getLastFragmentIncludeMainTabs();
        if(top==null || top.getCurrentAccount()!=observing)return false;
        if(top instanceof ChatActivity && ((ChatActivity)top).getDialogId()==dialog
                && top.getCurrentAccount()==observing) return false;
        CameraPopState.Pending pending=a.state.get(dialog);
        if(a.config.respectMuted && CameraPopConfig.explicitlyMuted(observing,dialog,pending==null?0:pending.topic)) return false;
        if(!a.config.quiet)return true;
        long minute=System.currentTimeMillis()/60_000L;
        if(quietClockMinute!=minute) {
            Calendar now=Calendar.getInstance();quietMinute=now.get(Calendar.HOUR_OF_DAY)*60+now.get(Calendar.MINUTE);quietClockMinute=minute;
        }
        return !CameraPopState.quiet(quietMinute,a.config.quietStart,a.config.quietEnd);
    }
    private int unread(long dialog) {
        TLRPC.Dialog value=MessagesController.getInstance(observing).dialogs_dict.get(dialog);
        if(value==null) return -1; // Cache not loaded: postpone, do not invent an unread count.
        return value.unread_count; // Native dialog counter is authoritative, including forums.
    }
    private void observe(int account) {
        if(observing==account) return;
        stop();observing=account;
        for(int event:EVENTS) NotificationCenter.getInstance(account).addObserver(this,event);
        NotificationCenter.getGlobalInstance().addObserver(this,NotificationCenter.didSetPasscode);
        NotificationCenter.getGlobalInstance().addObserver(this,NotificationCenter.passcodeDismissed);
        globals=true;
    }
    private void stop() {
        int previousAccount=observing;
        foregroundIslandAccount=-1;AndroidUtilities.cancelRunOnUIThread(indexNext);indexing=null;indexAccount=-1;
        flushSaves();
        if(observing>=0) {
            for(int event:EVENTS) NotificationCenter.getInstance(observing).removeObserver(this,event);
            AccountState a=accounts.get(observing);if(a!=null)a.state.clearQueue();
        }
        if(globals) {
            NotificationCenter.getGlobalInstance().removeObserver(this,NotificationCenter.didSetPasscode);
            NotificationCenter.getGlobalInstance().removeObserver(this,NotificationCenter.passcodeDismissed);
            globals=false;
        }
        observing=-1;hide();
        sessionAccount=-1;entryPending.clear();livePending.clear();liveRetries.clear();
        AndroidUtilities.cancelRunOnUIThread(reconcile);
        reconcileScheduled=false;
        AndroidUtilities.cancelRunOnUIThread(deadline);
        if(previousAccount>=0 && previousAccount!=UserConfig.selectedAccount && UserConfig.getInstance(previousAccount).isClientActivated())
            org.telegram.messenger.NotificationsController.getInstance(previousAccount).showNotifications();
    }
    private void saveSoon(int id) {
        if(host.get()==null) {AccountState a=account(id);a.config.save(a.state);return;}
        boolean first=dirtyAccounts.isEmpty();dirtyAccounts.add(id);
        if(first)AndroidUtilities.runOnUIThread(persist,600);
    }
    private void flushSaves() {
        AndroidUtilities.cancelRunOnUIThread(persist);
        for(int id:dirtyAccounts) {
            AccountState a=accounts.get(id);if(a!=null && a.config.enabled)a.config.save(a.state);
        }
        dirtyAccounts.clear();
    }
    private void reconcile() {
        AndroidUtilities.cancelRunOnUIThread(reconcile);reconcileScheduled=false;
        LaunchActivity activity=host.get();if(activity==null)return;
        int id=UserConfig.selectedAccount;
        if(!UserConfig.getInstance(id).isClientActivated() || !CameraPopConfig.enabled(id)) {stop();return;}
        observe(id);AccountState a=account(id);
        if(sessionAccount!=id) {
            sessionAccount=id;a.candidates.clear();a.inbox.clear();a.boundRevision=-1;a.indexedSize=-1;
            for(CameraPopState.Pending p:a.state.pending())a.candidates.add(p.dialog);
            if(!a.config.allChats)a.candidates.addAll(a.config.selected);
            entryPending.addAll(a.candidates);
        }
        if(safeWindow(activity)) {
            if(foregroundIslandAccount!=id){foregroundIslandAccount=id;refreshAndroid();}
        } else foregroundIslandAccount=-1;
        prepareIndex(a,id);
        boolean dirty=false;
        // Recover pending reminders from the selected native dialogs after process death.
        // This does not turn old unread messages into new-message alerts.
        for(long dialog:new HashSet<>(a.candidates)) {
            TLRPC.Dialog value=MessagesController.getInstance(id).dialogs_dict.get(dialog);
            CameraPopState.Pending p=a.state.get(dialog);
            if(value!=null && value.unread_count>0 && (p==null || p.due==0)) {
                dirty|=a.state.seed(dialog,value.top_message,System.currentTimeMillis(),a.config.interval());
            }
            if(value!=null && value.unread_count==0 && !waitingForCounter(a,dialog)) {
                entryPending.remove(dialog);livePending.remove(dialog);liveRetries.remove(dialog);
                a.candidates.remove(dialog);a.inbox.update(dialog,0,false);
            }
            else if(value!=null && value.unread_count>0 && ((a.config.reminders && entryPending.contains(dialog))
                    || (a.config.immediate && livePending.contains(dialog))) && allowed(a,dialog)) {
                if(capsule==null)a.state.enqueue(dialog);
            }
        }
        for(CameraPopState.Pending p:a.state.pending()) {
            if(p.due>0 && unread(p.dialog)==0 && !waitingForCounter(a,p.dialog)) {a.state.read(p.dialog);dirty=true;}
        }
        if(dirty)a.config.save(a.state);
        if(capsule!=null && !demo) {
            refreshInbox(a);
            if(a.inbox.size()==0)capsule.exit(this::hide);
            else bind(a,visibleDialog);
        }
        if(capsule==null && a.config.durationSeconds==0) {
            refreshInbox(a);
            if(a.inbox.size()>0)a.state.enqueue(a.inbox.newest());
        }
        deadline();
    }
    private void deadline() {
        if(observing<0 || host.get()==null) return;
        AccountState a=account(observing);long now=System.currentTimeMillis();boolean dirty=false;
        if(a.config.reminders) {
            for(CameraPopState.Pending p:a.state.pending()) {
                if(p.due<=0 || p.due>now) continue;
                int count=unread(p.dialog);
                if(count==0 && !waitingForCounter(a,p.dialog)) a.state.read(p.dialog);
                else {
                    if(count>0 && allowed(a,p.dialog)) a.state.enqueue(p.dialog);
                    a.state.defer(p.dialog,now+a.config.interval());
                }
                dirty=true;
            }
        }
        if(dirty)a.config.save(a.state);
        if(capsule==null) requestDrain(120);else a.state.clearQueue();
        schedule();
    }
    private void schedule() {
        AndroidUtilities.cancelRunOnUIThread(deadline);
        if(observing<0 || host.get()==null) return;
        AccountState a=account(observing);
        if(!a.config.reminders)return;
        long due=a.state.nextDue();
        if(due!=Long.MAX_VALUE) AndroidUtilities.runOnUIThread(deadline,Math.max(1000,due-System.currentTimeMillis()));
    }
    private void drain() {
        if(capsule!=null || observing<0)return;
        AccountState a=account(observing);long dialog;
        while((dialog=a.state.poll())!=0) {
            if(!allowed(a,dialog))continue;
            if(unread(dialog)<=0) {
                Integer attempts=liveRetries.get(dialog);
                if(attempts!=null && attempts>0 && waitingForCounter(a,dialog)) {
                    liveRetries.put(dialog,attempts-1);a.state.enqueue(dialog);requestDrain(120);return;
                }
                continue;
            }
            LaunchActivity activity=host.get();if(activity==null || !createCapsule(activity))return;
            visibleDialog=dialog;demo=false;refreshInbox(a);
            if(a.inbox.size()==0){hide();return;}
            bind(a,dialog);a.state.clearQueue();startCapsule();return;
        }
    }
    private boolean waitingForCounter(AccountState a,long dialog) {
        CameraPopState.Pending p=a.state.get(dialog);
        Integer read=MessagesController.getInstance(observing).dialogs_read_inbox_max.get(dialog);
        return livePending.contains(dialog) && p!=null && p.received>0 && (read==null || read<p.received);
    }
    private void requestDrain(long delay) {
        // A continuous stream must not keep pushing the first alert into the future.
        if(drainScheduled)return;
        drainScheduled=true;AndroidUtilities.runOnUIThread(drain,delay);
    }
    private boolean createCapsule(LaunchActivity activity) {
        View decor=activity.getWindow().getDecorView();
        if(!(decor instanceof FrameLayout))return false;
        FrameLayout root=(FrameLayout)decor;
        capsule=new CameraPopCapsule(root);
        FrameLayout.LayoutParams params=new FrameLayout.LayoutParams(AndroidUtilities.dp(360),FrameLayout.LayoutParams.WRAP_CONTENT,android.view.Gravity.TOP|android.view.Gravity.LEFT);
        root.addView(capsule,params);capsule.setAlpha(0f);
        capsule.setOnClickListener(v->open());return true;
    }
    private void bind(AccountState a,long dialog) {
        if(capsule==null || a.boundRevision==a.inbox.revision())return;
        a.boundRevision=a.inbox.revision();
        java.util.List<CameraPopInbox.Row> snapshot=a.inbox.snapshot();
        capsule.bindRows(observing,a.config.names,snapshot,this::openChat,this::expansionChanged);
        if(capsule.isExiting()){capsule.enter();armExpiry();}
        for(CameraPopInbox.Row row:snapshot) {
            entryPending.remove(row.dialog);livePending.remove(row.dialog);liveRetries.remove(row.dialog);
        }
        a.state.clearQueue();
    }
    private void refreshInbox(AccountState a) {
        Set<Long> visible=new HashSet<>();
        for(long dialog:a.candidates) {
            int count=unread(dialog);
            if(count>0 && allowed(a,dialog)) {visible.add(dialog);a.inbox.update(dialog,count,false);}
        }
        a.inbox.retain(visible);
    }
    private void expansionChanged() {
        AndroidUtilities.cancelRunOnUIThread(expire);
        if(capsule!=null && !capsule.isExpanded())armExpiry();
    }
    private void armExpiry() {
        AndroidUtilities.cancelRunOnUIThread(expire);
        int seconds=demo?5:account(observing).config.durationSeconds;
        if(seconds>0)AndroidUtilities.runOnUIThread(expire,seconds*1000L);
    }
    private void startCapsule() {
        if(!demo) {
            entryPending.remove(visibleDialog);livePending.remove(visibleDialog);liveRetries.remove(visibleDialog);
            AccountState a=account(observing);a.state.defer(visibleDialog,System.currentTimeMillis()+a.config.interval());saveSoon(observing);
        }
        capsule.enter();armExpiry();
    }
    private void expire() {
        if(capsule==null || capsule.isExpanded())return;
        capsule.exit(this::hide);
    }
    private void hide() {
        AndroidUtilities.cancelRunOnUIThread(expire);AndroidUtilities.cancelRunOnUIThread(drain);
        drainScheduled=false;
        if(capsule!=null) {CameraPopCapsule old=capsule;capsule=null;old.release();}
        if(observing>=0)account(observing).boundRevision=-1;
        visibleDialog=0;demo=false;
    }
    private void open() {if(capsule!=null)capsule.toggleExpanded();}
    private void openChat(long dialog) {
        LaunchActivity activity=host.get();boolean fictitious=demo;
        if(activity==null || !safeWindow(activity)) {hide();return;}
        int id=observing;hide(); // Cancel all motion before native navigation; no second tap.
        if(fictitious || id<0 || id!=UserConfig.selectedAccount)return;
        Bundle args=new Bundle();
        if(DialogObject.isUserDialog(dialog))args.putLong("user_id",dialog);
        else if(DialogObject.isChatDialog(dialog))args.putLong("chat_id",-dialog);
        else return;
        BaseFragment last=LaunchActivity.getLastFragmentIncludeMainTabs();
        if(last!=null && MessagesController.getInstance(id).checkCanOpenChat(args,last)) last.presentFragment(new ChatActivity(args));
    }
    private void requestReconcile() {
        if(reconcileScheduled)return;
        reconcileScheduled=true;AndroidUtilities.runOnUIThread(reconcile,80);
    }
    private void prepareIndex(AccountState a,int id) {
        if(!a.config.allChats)return;
        ArrayList<TLRPC.Dialog> dialogs=MessagesController.getInstance(id).getAllDialogs();
        if(a.indexedSize==dialogs.size())return;
        a.indexedSize=dialogs.size();indexing=new ArrayList<>(dialogs);indexPosition=indexing.size()-1;indexAccount=id;
        AndroidUtilities.cancelRunOnUIThread(indexNext);AndroidUtilities.runOnUIThread(indexNext,8);
    }
    private void indexNext() {
        if(indexing==null || observing!=indexAccount || host.get()==null)return;
        AccountState a=account(observing);int budget=96;boolean changed=false;
        while(indexPosition>=0 && budget-->0) {
            TLRPC.Dialog d=indexing.get(indexPosition--);
            if(d.unread_count>0 && (DialogObject.isUserDialog(d.id)||DialogObject.isChatDialog(d.id))) {
                a.candidates.add(d.id);entryPending.add(d.id);
                a.inbox.update(d.id,d.unread_count,true);
                changed|=a.state.seed(d.id,d.top_message,System.currentTimeMillis(),a.config.interval());
            }
        }
        if(changed)saveSoon(observing);
        requestReconcile();
        if(indexPosition>=0)AndroidUtilities.runOnUIThread(indexNext,8);else indexing=null;
    }
    /** Cross-thread route snapshot. It never accesses mutable UI collections. */
    public static boolean filtersAndroid(int id) {
        return CameraPopConfig.enabled(id) && (foregroundIslandAccount==id || CameraPopConfig.onlyIsland(id));
    }
    public static boolean routesToIsland(int id,MessageObject message) {
        if(message==null || message.messageOwner==null || message.isOutOwner() || message.isReactionPush
                || message.isStoryReactionPush || message.isOauthPush || message.isStoryPush
                || message.messageOwner.from_scheduled || message.isImportedForward()
                || DialogObject.isEncryptedDialog(message.getDialogId())
                || (message.messageOwner.action!=null && !(message.messageOwner.action instanceof TLRPC.TL_messageActionEmpty)))return false;
        return CameraPopConfig.interested(id,message.getDialogId())
                && (CameraPopConfig.onlyIsland(id) || foregroundIslandAccount==id);
    }
    private void refreshAndroid() {
        int id=UserConfig.selectedAccount;
        if(UserConfig.getInstance(id).isClientActivated())org.telegram.messenger.NotificationsController.getInstance(id).showNotifications();
    }
    @Override public void didReceivedNotification(int event,int account,Object...args) {
        if(event==NotificationCenter.dialogsNeedReload && args.length>0 && Boolean.TRUE.equals(args[0]) && observing>=0)
            account(observing).indexedSize=-1;
        if(event==NotificationCenter.didReceiveNewMessages) {
            if(account!=observing || args.length<4 || !Boolean.FALSE.equals(args[2])
                    || !(args[3] instanceof Integer) || (Integer)args[3]!=ChatActivity.MODE_DEFAULT
                    || !(args[1] instanceof ArrayList<?>))return;
            for(Object item:(ArrayList<?>)args[1])if(item instanceof MessageObject)incoming(account,(MessageObject)item);
            return;
        }
        if(event==NotificationCenter.appDidLogout) {
            AccountState a=accounts.remove(account);if(a!=null)a.config.clearPending();stop();return;
        }
        if(event==NotificationCenter.didSetPasscode || event==NotificationCenter.passcodeDismissed)hide();
        requestReconcile();
    }
}
