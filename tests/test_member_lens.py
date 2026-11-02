"""Quick Member Lens host regressions. Java host doubles are not an Android application run."""
from pathlib import Path
import subprocess,tempfile,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/'TMessagesProj/src/main/java'
BASE='bf96667efac14d0cbbf6677471890a366c3ef3c0'
def source(p):return (J/p).read_text()
def method(s,anchor):
 a=s.index(anchor);i=s.index('{',a)+1;level=1
 while level:level+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[a:i]
def execute(name,code):
 with tempfile.TemporaryDirectory()as tmp:
  p=Path(tmp)/(name+'.java');p.write_text(code)
  result=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(J/'app/flexygram/memberlens/MemberLensScope.java'),str(p)],capture_output=True,text=True)
  assert result.returncode==0,result.stderr
  return subprocess.check_output(['java','-cp',tmp,name],text=True)
def test_real_scope_keeps_long_ids_and_rejects_anonymous_cross_group_results():
 assert 'PASS' in execute('ScopeProbe','''import app.flexygram.memberlens.MemberLensScope;
 public class ScopeProbe{public static void main(String[]a){
 var s=new MemberLensScope(2,-9000000001L,8000000002L,17);
 if(!s.accepts(-9000000001L,8000000002L)||s.accepts(-9000000002L,8000000002L)||s.accepts(s.dialogId,-s.userId)||s.accepts(s.dialogId,123))throw new AssertionError();
 if(s.key().equals(new MemberLensScope(1,s.dialogId,s.userId,17).key())||s.key().equals(new MemberLensScope(2,s.dialogId,s.userId,18).key()))throw new AssertionError();
 int rejected=0;for(long d:new long[]{0,1,Long.MIN_VALUE})try{new MemberLensScope(0,d,1,0);}catch(IllegalArgumentException ok){rejected++;}
 for(long u:new long[]{0,-1})try{new MemberLensScope(0,-1,u,0);}catch(IllegalArgumentException ok){rejected++;}
 try{new MemberLensScope(0,-1,1,-1);}catch(IllegalArgumentException ok){rejected++;}if(rejected!=6)throw new AssertionError();System.out.println("PASS");}}''')
def test_actual_dispose_cancels_only_lens_request_invalidates_generation_and_clears_models():
 body=method(source('org/telegram/ui/FilteredSearchView.java'),'public void disposeMemberLens()')
 assert 'PASS' in execute('DisposeProbe','''import java.util.*;import app.flexygram.memberlens.MemberLensScope;
 public class DisposeProbe{
 MemberLensScope memberLensScope=new MemberLensScope(2,-44,66,0);boolean memberLensDisposed;int requestIndex=7,memberLensRequestId=91;
 Runnable searchRunnable=()->{},clearCurrentResultsRunnable=()->{},hideFloatingDateRunnable=()->{},memberLensState;Object memberLensNavigate;
 ArrayList<Object> messages=new ArrayList<>(),messagesById=new ArrayList<>(),sections=new ArrayList<>(),sectionArrays=new ArrayList<>();
 static class AndroidUtilities{static int canceled;static void cancelRunOnUIThread(Runnable r){canceled++;}}
 static class ConnectionsManager{static int account,token,calls;static ConnectionsManager getInstance(int a){account=a;return new ConnectionsManager();}void cancelRequest(int t,boolean force){token=t;calls++;}}
 static class ListView{void setAdapter(Object a){}}ListView recyclerListView=new ListView();
 '''+body+'''public static void main(String[]a){var p=new DisposeProbe();p.messages.add(new Object());p.disposeMemberLens();p.disposeMemberLens();if(!p.memberLensDisposed||p.requestIndex!=8||p.memberLensRequestId!=0||ConnectionsManager.calls!=1||ConnectionsManager.account!=2||ConnectionsManager.token!=91||AndroidUtilities.canceled!=3||!p.messages.isEmpty())throw new AssertionError();System.out.println("PASS");}}''')
def test_actual_snapshot_restores_loaded_cursor_and_refuses_different_scope():
 s=source('org/telegram/ui/FilteredSearchView.java')
 pieces='\n'.join(method(s,a)for a in ['public static final class MemberLensSnapshot','public MemberLensSnapshot saveMemberLensState()','public boolean restoreMemberLensState('])
 code='''import java.util.*;import app.flexygram.memberlens.MemberLensScope;
 public class FilteredSearchView{
 MemberLensScope memberLensScope=new MemberLensScope(1,-33,9000000001L,17);
 String currentSearchString="photo",lastMessagesSearchString,lastSearchFilterQueryString;long currentSearchDialogId;int memberLensOffset=50,totalCount=100;boolean endReached,isLoading,firstLoading;
 static class MessageObject{int id;MessageObject(int n){id=n;}int getId(){return id;}}
 ArrayList<MessageObject> messages=new ArrayList<>();HashMap<Integer,MessageObject> messagesById=new HashMap<>();
 static class Adapter{void notifyDataSetChanged(){}}Adapter adapter=new Adapter();void memberLensStateChanged(){}
 '''+pieces+'''
 public static void main(String[]args){var old=new FilteredSearchView();old.messages.add(new MessageObject(50));var saved=old.saveMemberLensState();old.messages.clear();var fresh=new FilteredSearchView();if(!fresh.restoreMemberLensState(saved,"photo")||fresh.messages.size()!=1||fresh.memberLensOffset!=50||fresh.totalCount!=100)throw new AssertionError();
 var different=new FilteredSearchView();different.memberLensScope=new MemberLensScope(1,-33,9000000001L,18);if(different.restoreMemberLensState(saved,"photo")||!different.messages.isEmpty())throw new AssertionError();if(different.restoreMemberLensState(saved,"wrong"))throw new AssertionError();System.out.println("PASS");}}
 '''
 assert 'PASS' in execute('FilteredSearchView',code)
def test_native_request_uses_sender_topic_cursor_and_pinned_account():
 s=source('org/telegram/ui/FilteredSearchView.java')
 assert 'req.from_id=AccountInstance.getInstance(currentAccount).getMessagesController().getInputPeer(memberLensScope.userId);req.flags|=1' in s
 assert 'req.top_msg_id=memberLensScope.topicId;req.flags|=2' in s
 assert 'if(memberLensScope!=null)req.offset_id=memberLensOffset' in s
 assert 'memberLensScope==null?UserConfig.selectedAccount:memberLensScope.account' in s
 assert 'req.limit = 20' in s and 'req.filter = currentSearchFilter == null ? new TLRPC.TL_inputMessagesFilterEmpty()' in s
 assert 'memberLensScope.topicId!=0 && MessageObject.getTopicId' in s
 assert 'message.messageOwner.from_id.user_id' in s
 assert 'fwd_from' not in method(s,'public void configureMemberLens(')
def test_pagination_only_inserts_rows_and_old_responses_are_rejected():
 s=source('org/telegram/ui/FilteredSearchView.java')
 assert 'if (!clearOldResults && (isLoading || endReached || memberLensFailed)) return' in s
 assert 'if (requestId != requestIndex)' in s
 assert s.index('if (requestId != requestIndex)')<s.index('int oldLensSize=messages.size()')
 assert 'adapter.notifyItemRangeInserted(oldLensSize,messages.size()-oldLensSize)' in s
 assert 'messagesById.get(messageObject.getId())!=null' in s
 assert 'messageObjects.size()<20 || next==memberLensOffset' in s
 assert 'memberLensRequestId!=0)ConnectionsManager.getInstance(memberLensScope.account).cancelRequest' in s
 assert 'retryMemberLens()' in s
 assert 'boolean firstPage=messages.isEmpty();memberLensFailed=false' in method(s,'public void retryMemberLens()')
 assert 'currentSearchString,firstPage)' in method(s,'public void retryMemberLens()')
 assert 'return; // No per-row enter animations' in s

def test_avatar_normal_tap_is_identical_and_lens_gates_real_sender():
 path='org/telegram/ui/ChatActivity.java';s=source(path)
 original=subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/java/'+path],cwd=ROOT,text=True)
 assert method(s,'public void didPressUserAvatar(')==method(original,'public void didPressUserAvatar(')
 gate=method(s,'private boolean canOpenMemberLens(')
 for text in ['MemberLensConfig.enabled()','ChatObject.isChannelAndNotMegaGroup','ChatObject.isMonoForum','message.messageOwner.from_id.user_id==user.id','isThreadChat()&&!isTopic','searching']:
  assert text in gate
 assert 'memberLens ? 1 : 0' in s and 'case MEMBER_LENS:' in s
 assert 'args.putLong("lens_user",user.id)' in s

def test_direct_chat_toggle_only_one_location_and_existing_store():
 s=source('app/flexygram/settings/signature/SignatureDirectSettingsActivity.java')
 assert s.count('new app.flexygram.memberlens.MemberLensSettingsSection()')==1
 assert s.index('case "chat":')<s.index('new app.flexygram.memberlens.MemberLensSettingsSection()')<s.index('case "home":')
 config=source('app/flexygram/memberlens/MemberLensConfig.java')
 assert 'NekoConfig.getPreferences()' in config and 'getBoolean(KEY,false)' in config and '.apply()' in config
 section=source('app/flexygram/memberlens/MemberLensSettingsSection.java')
 assert 'notifyItemChanged(enabledRow)' in section

def test_original_is_retained_and_filtered_cells_are_native():
 activity=source('app/flexygram/memberlens/MemberLensActivity.java')
 assert 'WeakReference<ChatActivity>' in activity
 assert 'chat.openMemberLensOriginal(message.getId())' in activity and 'finishFragment();' in activity
 for forbidden in ['loadMessages(','clearHistory','saveDraft(','markDialogAsRead','switchAccount(','searchMessagesInChat(']:assert forbidden not in activity
 s=method(source('org/telegram/ui/FilteredSearchView.java'),'public void configureMemberLens(')
 assert 'new org.telegram.ui.Cells.ChatMessageCell' in s and 'cell.setMessageObject(message,null,false,false,false)' in s
 assert 'LocaleController.formatDateChat' in s
 assert 'MemberLensGoTo' in s
 assert 'recyclerListView.setEmptyView(null)' in s

def test_locales_and_no_new_manifest_signing_distribution_changes():
 sets=[]
 for folder in ['values','values-es','values-ru']:
  values=list(E.parse(ROOT/'TMessagesProj/src/main/res'/folder/'flexy_member_lens.xml').getroot());assert len(values)==8 and all(v.text for v in values);sets.append({v.get('name')for v in values})
 assert sets[0]==sets[1]==sets[2]
 for path in ['TMessagesProj/src/main/AndroidManifest.xml','TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java','gradle/flexygram-beta.gradle']:
  assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)

def test_actual_protocol_scope_block_sets_person_topic_flags_without_narrowing_ids():
 s=source('org/telegram/ui/FilteredSearchView.java')
 block=method(s,'if(memberLensScope!=null){\n                    req.from_id')
 assert 'PASS' in execute('RequestProbe','''import app.flexygram.memberlens.MemberLensScope;
 public class RequestProbe{
 static class Req{long from_id;int flags,top_msg_id;}
 static class AccountInstance{static int account;static AccountInstance getInstance(int n){account=n;return new AccountInstance();}AccountInstance getMessagesController(){return this;}long getInputPeer(long id){return id;}}
 MemberLensScope memberLensScope=new MemberLensScope(2,-44,9000000001L,77);int currentAccount=2;
 void configure(Req req){'''+block+'''}
 public static void main(String[]args){var p=new RequestProbe();var req=new Req();p.configure(req);if(req.from_id!=9000000001L||req.top_msg_id!=77||req.flags!=3||AccountInstance.account!=2)throw new AssertionError();
 p.memberLensScope=new MemberLensScope(2,-44,9,0);req=new Req();p.configure(req);if(req.flags!=1||req.top_msg_id!=0)throw new AssertionError();System.out.println("PASS");}}
 ''')
