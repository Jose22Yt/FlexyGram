"""The classes under test are copied verbatim. Services and the inherited settings host are doubles.
Screenshots show the actual new demo/span renderer, not the whole Telegram application.
"""
import re,json,xml.etree.ElementTree as ET

def write(dest,root):
 def emit(path,s):
  p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 java=root/'TMessagesProj/src/main/java';code=''
 for name in ['SignatureSmartPreviewPalette','SignatureSmartPreviews','SignatureSmartPillSpan','SignaturePreviewIcon','SignatureMiniPillClassifier','SmartPreviewsDemoView','SmartPreviewsSettingsActivity']:
  path='app/flexygram/home/'+name+'.java';s=(java/path).read_text();emit(path,s);code+=s
 strings=sorted(set(re.findall(r'R.string.(\w+)',code)));titles={}
 for directory in ['values','values-es']:
  for p in (root/'TMessagesProj/src/main/res'/directory).glob('*.xml'):
   for e in ET.parse(p).getroot().findall('string'):
    if e.get('name')in strings:titles[e.get('name')]=''.join(e.itertext()).replace("\\'","'")
 emit('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class string{'+''.join('public static final int '+n+'='+str(i+1)+';'for i,n in enumerate(strings))+'}}')
 emit('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController{public static boolean isRTL;public static String getString(int id){return switch(id){'+''.join('case '+str(i+1)+'->'+json.dumps(titles[n],ensure_ascii=True)+';'for i,n in enumerate(strings))+'default->"";};}}')
 emit('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities{public static float density=1;public static int dp(float n){return Math.round(n*density);}public static android.graphics.Typeface getTypeface(String s){return android.graphics.Typeface.DEFAULT;}}')
 emit('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}')
 emit('org/telegram/messenger/FileLoader.java','package org.telegram.messenger;public class FileLoader{public static String getDocumentFileName(org.telegram.tgnet.TLRPC.Document d){return d==null?null:d.name;}}')
 emit('org/telegram/tgnet/TLRPC.java',r'''package org.telegram.tgnet;import java.util.*;public class TLRPC{
 public static class Document{public String name,mime_type;}public static class MessageEntity{}public static class TL_messageEntitySpoiler extends MessageEntity{}
 public static class MessageMedia{public int ttl_seconds;public String first_name,last_name;}public static class TL_messageMediaContact extends MessageMedia{}public static class TL_messageMediaGeo extends MessageMedia{}public static class TL_messageMediaGeoLive extends MessageMedia{}public static class TL_messageMediaVenue extends MessageMedia{}public static class TL_messageMediaPoll extends MessageMedia{}
 public static class MessageAction{}public static class TL_messageActionChatAddUser extends MessageAction{}public static class TL_messageActionChatJoinedByLink extends MessageAction{}public static class TL_messageActionChatDeleteUser extends MessageAction{public long user_id;}public static class TL_messageActionPinMessage extends MessageAction{}
 public static class Peer{public long user_id;}public static class Message{public MessageMedia media;public ArrayList<Object> restriction_reason=new ArrayList<>();public ArrayList<MessageEntity> entities=new ArrayList<>();public MessageAction action;public Peer from_id;public boolean post;public int edit_date;public String message;}
 public static class ChannelParticipant{}public static class TL_channelParticipantCreator extends ChannelParticipant{}public static class TL_channelParticipantAdmin extends ChannelParticipant{}
 public static class ChatParticipant{public long user_id;}public static class TL_chatParticipantCreator extends ChatParticipant{}public static class TL_chatParticipantAdmin extends ChatParticipant{}public static class Participants{public ArrayList<ChatParticipant>participants=new ArrayList<>();}public static class ChatFull{public Participants participants;}}
''')
 emit('org/telegram/messenger/MessageObject.java',r'''package org.telegram.messenger;import org.telegram.tgnet.TLRPC;public class MessageObject{
 public TLRPC.Message messageOwner=new TLRPC.Message();public int currentAccount;public CharSequence messageText;public boolean highlighted,blurred,voice,music,video,photo,sticker,gif,document,deleted;public TLRPC.Document doc;public double duration;public String title;public long dialog;
 public boolean hasHighlightedWords(){return highlighted;}public boolean needDrawBluredPreview(){return blurred;}public boolean isVoice(){return voice;}public boolean isMusic(){return music;}public boolean isVideo(){return video;}public boolean isPhoto(){return photo;}public boolean isSticker(){return sticker;}public boolean isGif(){return gif;}public boolean isDocument(){return document;}public boolean isAyuDeleted(){return deleted;}public TLRPC.Document getDocument(){return doc;}public long getDialogId(){return dialog;}public double getDuration(){return duration;}public String getMusicTitle(){return title;}}
''')
 emit('org/telegram/messenger/MessagesController.java','package org.telegram.messenger;import org.telegram.tgnet.TLRPC;public class MessagesController{public static MessagesController getInstance(int a){throw new AssertionError("No account initialization in local preview");}public TLRPC.ChannelParticipant getAdminInChannel(long s,long c){return null;}public TLRPC.ChatFull getChatFull(long c){return null;}}')
 emit('org/telegram/ui/ActionBar/Theme.java',r'''package org.telegram.ui.ActionBar;public class Theme{
 public interface Colorable{void updateColors();}public interface ResourcesProvider{int getColor(int key);}
 public static final int key_actionBarTabLine=1,key_windowBackgroundWhite=2,key_windowBackgroundWhiteBlackText=3;
 public static int surface=0xff101820,accent=0xff3b82f6;public static int getColor(int k,ResourcesProvider p){return p!=null?p.getColor(k):k==1?accent:k==2?surface:0xffffffff;}}
''')
 emit('org/telegram/ui/ActionBar/ThemeDescription.java','package org.telegram.ui.ActionBar;public class ThemeDescription{public interface ThemeDescriptionDelegate{void didSetColor();}public ThemeDescription(android.view.View v,int f,Class[] c,String[] n,android.graphics.Paint[] p,android.graphics.drawable.Drawable[]d,ThemeDescriptionDelegate a,int k){}}')
 emit('org/telegram/ui/Components/RecyclerListView.java','package org.telegram.ui.Components;import androidx.recyclerview.widget.RecyclerView;public class RecyclerListView extends RecyclerView{public RecyclerListView(android.content.Context c){super(c);}public static class Holder extends RecyclerView.ViewHolder{public Holder(android.view.View v){super(v);}}public abstract static class SelectionAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder>{public abstract boolean isEnabled(RecyclerView.ViewHolder h);}}')
 emit('org/telegram/ui/Cells/TextRadioCell.java','package org.telegram.ui.Cells;public class TextRadioCell extends android.widget.RadioButton{public TextRadioCell(android.content.Context c){super(c);setMinHeight(48);}public void setTextAndCheck(String t,boolean b,boolean d){setText(t);setChecked(b);}}')
 emit('tw/nekomimi/nekogram/ui/cells/HeaderCell.java','package tw.nekomimi.nekogram.ui.cells;public class HeaderCell extends android.widget.TextView{public HeaderCell(android.content.Context c){super(c);}}')
 emit('app/flexygram/settings/SignatureMatteSettingsActivity.java',r'''package app.flexygram.settings;import android.content.*;import android.view.*;import androidx.recyclerview.widget.*;import org.telegram.ui.Components.RecyclerListView;import org.telegram.ui.ActionBar.*;public abstract class SignatureMatteSettingsActivity{
 public int getSearchGuid(){return 0;}
 public static final Object PARTIAL=new Object();protected static final int TYPE_HEADER=4,TYPE_RADIO=10;protected int rowCount;protected BaseListAdapter listAdapter;protected Theme.ResourcesProvider resourcesProvider;protected RecyclerListView listView;
 protected int addRow(){return rowCount++;}protected int addRow(String key){return addRow();}protected void updateRows(){rowCount=0;}protected int settingsRowPosition(RecyclerView.ViewHolder h){return h.getBindingAdapterPosition();}
 protected abstract String getActionBarTitle();protected abstract BaseListAdapter createAdapter(Context c);protected abstract void onItemClick(View v,int p,float x,float y);
 public RecyclerListView createView(Context c){updateRows();listView=new RecyclerListView(c);listView.setLayoutManager(new LinearLayoutManager(c));listAdapter=createAdapter(c);listView.setAdapter(listAdapter);return listView;}public void click(int p){onItemClick(null,p,0,0);}public java.util.ArrayList<ThemeDescription>getThemeDescriptions(){return new java.util.ArrayList<>();}
 protected abstract class BaseListAdapter extends RecyclerListView.SelectionAdapter{protected final Context context;protected BaseListAdapter(Context c){context=c;}public int getItemCount(){return rowCount;}public void onBindViewHolder(RecyclerView.ViewHolder h,int p){onBindViewHolder(h,p,false);}public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){}public boolean isEnabled(RecyclerView.ViewHolder h){return true;}}
 protected abstract class MatteListAdapter extends BaseListAdapter{protected MatteListAdapter(Context c){super(c);}public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){return new RecyclerListView.Holder(type==TYPE_HEADER?new tw.nekomimi.nekogram.ui.cells.HeaderCell(context):new org.telegram.ui.Cells.TextRadioCell(context));}}
}
''')
 emit('app/flexygram/settings/signature/SignatureSettingsRegistry.java','package app.flexygram.settings.signature;public class SignatureSettingsRegistry{public static int searchGuid(String s){return 1000;}}')
 # Actual DialogCell policy method with explicit layout/services doubles; real Android View invalidation.
 s=(java/'org/telegram/ui/Cells/DialogCell.java').read_text();a=s.index('    private void refreshSmartPreviewStyle(');b=s.index('    public void buildLayout()',a);method=s[a:b].replace('private void refreshSmartPreviewStyle','public void refreshSmartPreviewStyle')
 emit('DialogStyleProbe.java',r'''import org.telegram.messenger.MessageObject;public class DialogStyleProbe extends android.view.View{public MessageObject message;public boolean isDialogCell=true,isTopic;public int smartPreviewKind,smartPreviewModeLastBuilt,builds;public DialogStyleProbe(android.content.Context c){super(c);}void buildLayout(){builds++;smartPreviewModeLastBuilt=app.flexygram.home.SignatureSmartPreviews.mode();smartPreviewKind=smartPreviewModeLastBuilt==3?0:app.flexygram.home.SignatureSmartPreviews.kind(message);}
'''+method+'}')


def resources(root,out):
 # Compile the actual referenced strings, not only the host-generated Java IDs.
 java=root/'TMessagesProj/src/main/java/app/flexygram/home'
 names=set()
 for name in ['SignatureSmartPreviews','SmartPreviewsSettingsActivity','SmartPreviewsDemoView']:
  names.update(re.findall(r'R.string.(\w+)',(java/(name+'.java')).read_text()))
 found={}
 for directory in ['values','values-es']:
  for p in (root/'TMessagesProj/src/main/res'/directory).glob('*.xml'):
   for x in ET.parse(p).getroot().findall('string'):
    if x.get('name') in names: found[x.get('name')]=x
 values=ET.Element('resources')
 for n in sorted(names): values.append(found[n])
 folder=out.parent/'values';folder.mkdir(exist_ok=True)
 ET.ElementTree(values).write(folder/'smart-previews.xml',encoding='utf-8',xml_declaration=True)
