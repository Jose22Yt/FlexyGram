"""Execute read-only wallet load/retry ownership and settings account contracts. No wallet keys/network."""
import re,xml.etree.ElementTree as ET
from pathlib import Path
from test_composer_layout import method
from test_render_work_reuse import JAVA,probe
W=JAVA/'org/telegram/ui/Wallet'


def test_wallet_load_tokens_reject_timeouts_cancelled_and_out_of_order_results(tmp_path):
    probe(tmp_path,{'Probe.java':'''import org.telegram.ui.Wallet.WalletLoadState;
public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){
 WalletLoadState s=new WalletLoadState();check(!s.isLoading()&&s.getError()==null);
 long first=s.begin();check(s.owns(first));check(s.finish(first,"timeout")&&!s.isLoading());
 long retry=s.begin();check(s.getError()==null&&!s.finish(first,null)&&s.owns(retry));
 check(s.finish(retry,null)&&!s.isLoading()&&s.getError()==null);check(!s.finish(retry,"late"));
 long cancelled=s.begin();s.cancel();check(!s.finish(cancelled,null));s.setError("engine");check(s.getError().equals("engine"));s.clearError();check(s.getError()==null);
 for(int i=0;i<1000;i++){long old=s.begin();s.cancel();long current=s.begin();check(!s.finish(old,"stale")&&s.owns(current));check(s.finish(current,null));}
}}'''},[W/'WalletLoadState.java'])


def test_real_wallet_request_failure_timeout_retry_and_creating_poll_are_bounded(tmp_path):
    source=(W/'GramWallet.java').read_text()
    methods='\n'.join(method(source,k) for k in ['private void requestState()','private void cancelStateTimeout()','public void retryState()','public boolean isStateLoading()','public boolean hasState()','public boolean isWalletCreating()','public boolean isWalletEmpty()','public String getStateError()','private void cancel()'])
    probe(tmp_path,{'Probe.java':'''import java.util.*;import java.util.function.*;import org.telegram.ui.Wallet.WalletLoadState;
class TL_wallet{static class WalletState{}static class TL_walletState extends WalletState{long balance;}static class TL_walletStateEmpty extends WalletState{boolean creating;}static class getState{}}
class Failure{String text;Failure(String text){this.text=text;}}
class Connection{int sends;Set<Integer>cancelled=new HashSet<>();ArrayList<BiConsumer<TL_wallet.WalletState,Failure>>calls=new ArrayList<>();
 int sendRequestTyped(TL_wallet.getState r,Consumer<Runnable>dispatch,BiConsumer<TL_wallet.WalletState,Failure>callback){sends++;calls.add(callback);return sends;}void cancelRequest(int id,boolean notify){cancelled.add(id);}}
class AndroidUtilities{static Map<Runnable,Long>pending=new HashMap<>();static void runOnUIThread(Runnable r){r.run();}static void runOnUIThread(Runnable r,long delay){pending.put(r,delay);}static void cancelRunOnUIThread(Runnable r){pending.remove(r);}}
public class Probe{
 int requestingGaslessInfoId=-1,requestingWaltId=-1;int requestingStateId=-1,creatingStateAttempts,updates,applies;WalletLoadState stateLoad=new WalletLoadState();Runnable stateRequestTimeout;
 String engineError;TL_wallet.WalletState state;boolean balanceFromStreaming;long streamingBalanceReceivedTime,serverBalanceReceivedTime;
 HashSet<Integer>listeningTokens=new HashSet<>();Connection connection=new Connection();Runnable refreshCreatingWallet=()->{if(!listeningTokens.isEmpty()&&isWalletCreating())requestState();};
 Connection getConnectionsManager(){return connection;}void log(String s){}void err(String s){}void onStateUpdate(){applies++;}void notifyUpdate(){updates++;}
 METHODS
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();p.requestState();Runnable timeout=p.stateRequestTimeout;
 check(p.isStateLoading()&&p.connection.sends==1);p.requestState();check(p.connection.sends==1);
 p.connection.calls.get(0).accept(null,new Failure("offline"));check(!p.isStateLoading()&&p.updates==1&&"offline".equals(p.getStateError())&&!AndroidUtilities.pending.containsKey(timeout));
 p.retryState();timeout.run();check(p.connection.sends==2&&p.getStateError()==null&&p.isStateLoading());p.connection.calls.get(0).accept(new TL_wallet.TL_walletState(),null);check(p.state==null&&p.isStateLoading());
 p.stateRequestTimeout.run();check(!p.isStateLoading()&&p.connection.cancelled.contains(2)&&"WALLET_STATE_TIMEOUT".equals(p.getStateError()));
 p.retryState();p.connection.calls.get(1).accept(new TL_wallet.TL_walletState(),null);check(p.state==null&&p.isStateLoading());
 TL_wallet.TL_walletState valid=new TL_wallet.TL_walletState();valid.balance=7;p.connection.calls.get(2).accept(valid,null);check(p.state==valid&&!p.isStateLoading()&&p.getStateError()==null);
 p.balanceFromStreaming=true;p.streamingBalanceReceivedTime=System.currentTimeMillis();p.retryState();TL_wallet.TL_walletState stale=new TL_wallet.TL_walletState();stale.balance=1;p.connection.calls.get(3).accept(stale,null);check(stale.balance==7);
 Probe creating=new Probe();creating.listeningTokens.add(1);TL_wallet.TL_walletStateEmpty empty=new TL_wallet.TL_walletStateEmpty();empty.creating=true;
 for(int i=0;i<10;i++){creating.requestState();creating.connection.calls.get(i).accept(empty,null);if(i<9)check(AndroidUtilities.pending.remove(creating.refreshCreatingWallet)!=null);}
 check(!AndroidUtilities.pending.containsKey(creating.refreshCreatingWallet)&&"WALLET_INITIALIZING".equals(creating.getStateError()));
 creating.listeningTokens.clear();creating.refreshCreatingWallet.run();check(creating.connection.sends==10);
 Probe cancelled=new Probe();cancelled.requestState();Runnable abandoned=cancelled.stateRequestTimeout;cancelled.cancel();check(!cancelled.isStateLoading()&&!AndroidUtilities.pending.containsKey(abandoned));cancelled.retryState();abandoned.run();cancelled.connection.calls.get(0).accept(valid,null);check(cancelled.state==null&&cancelled.isStateLoading());
 }}'''.replace('METHODS',methods)},[W/'WalletLoadState.java'])


def test_wallet_flag_respects_default_cache_and_server_boolean_in_debug_builds(tmp_path):
    source=(JAVA/'org/telegram/messenger/AppGlobalConfig.java').read_text()
    declaration=re.search(r'public final ConfigBoolean walletAvailable\s*=.*?;',source).group(0)
    boolean=method(source,'public static class ConfigBoolean')
    factory=method(source,'private ConfigBoolean ofBoolean(')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
interface SharedPreferences{boolean getBoolean(String name,boolean fallback);interface Editor{Editor putBoolean(String n,boolean v);}}
class TLRPC{static class JSONValue{}static class TL_jsonBool extends JSONValue{boolean value;TL_jsonBool(boolean v){value=v;}}}
public class Probe{
 interface ConfigInternal{boolean apply(SharedPreferences.Editor editor,TLRPC.JSONValue value);void load(SharedPreferences prefs);}
 HashMap<String,ConfigInternal>map=new HashMap<>();DECLARATION BOOLEAN FACTORY
 static class Editor implements SharedPreferences.Editor{boolean stored;public Editor putBoolean(String n,boolean value){stored=value;return this;}}
 public static void main(String[]args){Probe p=new Probe();ConfigInternal h=p.map.get("wallet_available");Editor e=new Editor();h.load((n,f)->f);
 if(p.walletAvailable.get())throw new AssertionError("unsupported wallet forced visible");h.apply(e,new TLRPC.TL_jsonBool(true));if(!p.walletAvailable.get()||!e.stored)throw new AssertionError();h.apply(e,new TLRPC.TL_jsonBool(false));if(p.walletAvailable.get())throw new AssertionError("server disable ignored");h.load((n,f)->true);if(!p.walletAvailable.get())throw new AssertionError("cached availability lost");}
}'''.replace('DECLARATION',declaration).replace('BOOLEAN',boolean).replace('FACTORY',factory)})


def test_settings_destinations_keep_owner_account_on_phone_and_tablet(tmp_path):
    source=(JAVA/'org/telegram/ui/SettingsActivity.java').read_text();actual=method(source,'private void presentSettingFragment(')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
class BaseFragment{int account;void setCurrentAccount(int a){account=a;}}
class AndroidUtilities{static boolean tablet;static boolean isTablet(){return tablet;}}
class INavigationLayout{ArrayList<BaseFragment>stack=new ArrayList<>();BaseFragment presented;static class NavigationParams{BaseFragment fragment;NavigationParams(BaseFragment f){fragment=f;}NavigationParams setNoAnimation(boolean v){return this;}NavigationParams forceRightLayout(){return this;}}ArrayList<BaseFragment>getFragmentStack(){return stack;}void removeFragmentFromStack(BaseFragment f){stack.remove(f);}void closeLastFragment(boolean a){stack.clear();}void presentFragment(NavigationParams p){presented=p.fragment;}}
class LaunchActivity{static LaunchActivity instance=new LaunchActivity();INavigationLayout layout=new INavigationLayout();INavigationLayout getRightActionBarLayout(){return layout;}}
public class Probe{int currentAccount;BaseFragment presented;void presentFragment(BaseFragment f){presented=f;}
 METHOD
 public static void main(String[]args){Probe p=new Probe();for(int account:new int[]{0,1,3}){p.currentAccount=account;for(boolean tablet:new boolean[]{false,true}){AndroidUtilities.tablet=tablet;BaseFragment f=new BaseFragment();p.presentSettingFragment(f);if(f.account!=account)throw new AssertionError("wrong settings/wallet account");if((tablet?LaunchActivity.instance.layout.presented:p.presented)!=f)throw new AssertionError();}}}
}'''.replace('METHOD',actual)})
    assert 'BirthdayController.getInstance(currentAccount).getState()' in source


def test_wallet_recovery_resources_and_error_rows_are_consistent():
    root=Path(__file__).resolve().parents[1]
    files=[root/f'TMessagesProj/src/main/res/{lang}/flexy_wallet_recovery.xml' for lang in ['values','values-es']]
    names=[{s.attrib['name'] for s in ET.parse(f).getroot()} for f in files]
    assert names[0]==names[1] and len(names[0])==6
    activity=(W/'WalletActivity.java').read_text()
    for name in names[0]: assert 'R.string.'+name in activity
    load=method(activity,'private void loadMoreTransactions()');assert 'transactionsList.getError() == null' in load
    fill=method(activity,'private void fillTransactions(');assert 'RETRY_TRANSACTIONS' in fill
    update=method(activity,'private void update()');assert 'wallet.isStateLoading() && !wallet.hasState()' in update


def test_transaction_requests_deduplicate_retry_and_ignore_cancelled_results(tmp_path):
    source=(W/'GramWallet.java').read_text();history=method(source,'public class TransactionsList')
    methods='\n'.join(method(history,k) for k in ['public void load()','public void invalidate()','public void cancel()','public boolean isLoading()','public boolean isEndReached()','public boolean isRefreshing()','public String getError()','public void retry()'])
    probe(tmp_path,{'Probe.java':'''import java.util.*;import java.util.function.*;
class TL_wallet{static class walletTransaction{String id;walletTransaction(String s){id=s;}boolean set(walletTransaction t){return false;}}static class getTransactions{boolean inbound,outbound;int limit;String offset;}}
class Failure{String text;Failure(String s){text=s;}}
class Result{ArrayList<Object>users=new ArrayList<>(),chats=new ArrayList<>();ArrayList<TL_wallet.walletTransaction>transactions=new ArrayList<>();String next_offset="next";}
class AndroidUtilities{static void runOnUIThread(Runnable r){r.run();}}
class MessagesController{static MessagesController getInstance(int a){return new MessagesController();}void putUsers(Object a,boolean b){}void putChats(Object a,boolean b){}}
class Connection{int sends;ArrayList<BiConsumer<Result,Failure>>calls=new ArrayList<>();Set<Integer>cancelled=new HashSet<>();int sendRequestTyped(TL_wallet.getTransactions r,Consumer<Runnable>d,BiConsumer<Result,Failure>c){calls.add(c);return ++sends;}void cancelRequest(int id,boolean n){cancelled.add(id);}}
class GramWallet{
 boolean ready=true;int currentAccount;Connection connection=new Connection();boolean isReady(){return ready;}Connection getConnectionsManager(){return connection;}
 public class TransactionsList{
  boolean loading,loadingInvalidation,endReached;long requestGeneration;String error,lastOffset="";int reqId=-1,invalidationReqId=-1,notifies,updates;
  ArrayList<TL_wallet.walletTransaction>transactions=new ArrayList<>();Set<String>streamTransactionIds=new HashSet<>();Map<String,Object>streamTraces=new HashMap<>();
  void appendOrReplace(TL_wallet.walletTransaction t){if(findTransactionById(transactions,t.id)==null)transactions.add(t);}void updatedTransactions(){updates++;}void notifyUpdate(){notifies++;}
  void insertStreamTransaction(TL_wallet.walletTransaction t){transactions.add(t);}TL_wallet.walletTransaction findTransactionById(ArrayList<TL_wallet.walletTransaction>a,String id){for(var t:a)if(t.id.equals(id))return t;return null;}
  METHODS
 }
}
public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){GramWallet w=new GramWallet();GramWallet.TransactionsList list=w.new TransactionsList();
  list.load();for(int i=0;i<1000;i++)list.load();check(w.connection.sends==1&&list.isLoading());
  w.connection.calls.get(0).accept(null,new Failure("offline"));check(!list.isLoading()&&!list.isEndReached()&&"offline".equals(list.getError()));
  list.retry();check(w.connection.sends==2&&list.isLoading()&&list.getError()==null);
  list.cancel();list.load();check(w.connection.sends==3);Result stale=new Result();stale.transactions.add(new TL_wallet.walletTransaction("stale"));w.connection.calls.get(1).accept(stale,null);check(list.transactions.isEmpty()&&list.isLoading());
  Result valid=new Result();valid.transactions.add(new TL_wallet.walletTransaction("valid"));w.connection.calls.get(2).accept(valid,null);check(!list.isLoading()&&list.transactions.size()==1&&list.transactions.get(0).id.equals("valid"));
  list.invalidate();for(int i=0;i<1000;i++)list.invalidate();check(w.connection.sends==4&&list.isRefreshing()&&!list.isLoading());
  list.cancel();list.invalidate();check(w.connection.sends==5);w.connection.calls.get(3).accept(new Result(),null);check(list.isRefreshing()&&list.transactions.size()==1);
  w.connection.calls.get(4).accept(null,new Failure("retry refresh"));check(!list.isLoading()&&!list.isRefreshing()&&list.transactions.size()==1&&"retry refresh".equals(list.getError()));
  list.retry();check(w.connection.sends==6&&list.isRefreshing());w.connection.calls.get(5).accept(valid,null);check(!list.isLoading()&&list.transactions.size()==1);
  list.cancel();w.ready=false;int requests=w.connection.sends;list.load();list.invalidate();check(w.connection.sends==requests);
 }
}'''.replace('METHODS',methods)})


def test_balance_updates_do_not_rebuild_wallet_history_and_status_rows(tmp_path):
    source=(W/'WalletActivity.java').read_text()
    methods='\n'.join(method(source,k) for k in ['private int walletPresentationFlags(','private boolean walletPresentationChanged(','private void rememberWalletPresentation('])
    probe(tmp_path,{'Probe.java':'''class GramWallet{boolean ready=true,loading,has=true,creating,empty;String error;long balance;boolean isReady(){return ready;}boolean isStateLoading(){return loading;}boolean hasState(){return has;}boolean isWalletCreating(){return creating;}boolean isWalletEmpty(){return empty;}String getStateError(){return error;}}
class Available{boolean value=true;boolean get(){return value;}}class Config{Available walletAvailable=new Available();}class MessagesController{Config config=new Config();}
public class Probe{int lastWalletPresentationFlags=Integer.MIN_VALUE;String lastWalletPresentationError;MessagesController controller=new MessagesController();MessagesController getMessagesController(){return controller;}
 METHODS
 static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){Probe p=new Probe();GramWallet w=new GramWallet();check(p.walletPresentationChanged(w));p.rememberWalletPresentation(w);
 for(int i=0;i<1000;i++){w.balance=i;check(!p.walletPresentationChanged(w));}
 w.loading=true;check(p.walletPresentationChanged(w));p.rememberWalletPresentation(w);check(!p.walletPresentationChanged(w));
 w.error="offline";check(p.walletPresentationChanged(w));p.rememberWalletPresentation(w);w.error=new String("offline");check(!p.walletPresentationChanged(w));
 p.controller.config.walletAvailable.value=false;check(p.walletPresentationChanged(w));
 }}'''.replace('METHODS',methods)})


def test_settings_list_refreshes_wallet_availability_and_balance_events(tmp_path):
    source=(JAVA/'org/telegram/ui/SettingsActivity.java').read_text()
    handler=method(source,'public void didReceivedNotification(').replace('@Override','')
    probe(tmp_path,{'Probe.java':'''class NotificationCenter{static final int starBalanceUpdated=1,updateInterfaces=2,newSuggestionsAvailable=3,appConfigUpdated=4,walletUpdate=5;}
class MessagesController{static final int UPDATE_MASK_NAME=1,UPDATE_MASK_AVATAR=2,UPDATE_MASK_PHONE=4,UPDATE_MASK_USER_PHONE=8,UPDATE_MASK_EMOJI_STATUS=16;}
public class Probe{int updates,info;boolean paused;boolean isPaused(){return paused;}void setInfo(){info++;}void scheduleItemsUpdate(boolean animated){updates++;}
 METHOD
 public static void main(String[]args){Probe p=new Probe();p.didReceivedNotification(NotificationCenter.appConfigUpdated,1);p.didReceivedNotification(NotificationCenter.walletUpdate,1);if(p.updates!=2||p.info!=0)throw new AssertionError("wallet settings did not refresh");}
}'''.replace('METHOD',handler)})
    for event in ['walletUpdate','appConfigUpdated']:
        assert f'addObserver(this, NotificationCenter.{event})' in source
        assert f'removeObserver(this, NotificationCenter.{event})' in source
    activity=(W/'WalletActivity.java').read_text();fill=method(activity,'private void fillTransactions(')
    assert 'transactionsList.getError() == null' in fill and 'isReady()' in fill


def test_wallet_child_navigation_keeps_the_account_before_initializing_destination(tmp_path):
    source=(W/'WalletActivity.java').read_text();actual=method(source,'public boolean presentFragment(BaseFragment fragment)')
    probe(tmp_path,{'Probe.java':'''class BaseFragment{int currentAccount;BaseFragment presented;int getCurrentAccount(){return currentAccount;}void setCurrentAccount(int account){currentAccount=account;}public boolean presentFragment(BaseFragment fragment){presented=fragment;return true;}}
public class Probe extends BaseFragment{
 METHOD
 public static void main(String[]args){Probe p=new Probe();p.currentAccount=3;BaseFragment child=new BaseFragment();if(!p.presentFragment(child)||child.getCurrentAccount()!=3||p.presented!=child)throw new AssertionError("wallet destination opened another account");}
}'''.replace('METHOD',actual)})
    assert source.index('sender.setCurrentAccount(fragment.getCurrentAccount())') < source.index('sender.setCollectible(collectible)')


def test_wallet_poll_callback_compiles_in_its_actual_field_initialization_order(tmp_path):
    source=(W/'GramWallet.java').read_text()
    declaration=re.search(r'private final Runnable refreshCreatingWallet\s*=\s*\(\)\s*->\s*\{.*?\n    \};',source,re.S).group(0)
    assert source.index(declaration)<source.index('private HashSet<Integer> listeningTokens')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
public class Probe{
 DECLARATION
 private HashSet<Integer> listeningTokens=new HashSet<>();int requests;
 boolean isWalletCreating(){return true;}void requestState(){requests++;}
 public static void main(String[]args){Probe p=new Probe();p.listeningTokens.add(1);p.refreshCreatingWallet.run();if(p.requests!=1)throw new AssertionError();p.listeningTokens.clear();p.refreshCreatingWallet.run();if(p.requests!=1)throw new AssertionError("poll after closing");}
}'''.replace('DECLARATION',declaration)})
