"""Explicit account/protocol/cell/service doubles. Real production transport/gates run;
Android graphics/codec/Views/Handler run under Robolectric. No server or full cell proof."""
def write(put):
 put('org/telegram/tgnet/TLRPC.java',r'''package org.telegram.tgnet;import java.util.*;public class TLRPC{
 public static class Document{public long id,size;public String mime_type;public byte[] file_reference;public ArrayList<DocumentAttribute> attributes=new ArrayList<>();}
 public static class TL_document extends Document{}public static class DocumentAttribute{public int w,h;public String alt;public Object stickerset;}
 public static class TL_documentAttributeImageSize extends DocumentAttribute{}public static class TL_documentAttributeSticker extends DocumentAttribute{}
 public static class TL_inputStickerSetEmpty{}public static class MessageEntity{}public static class TL_messageEntitySpoiler extends MessageEntity{}
 public static class MessageMedia{public Document document;}public static class TL_messageMediaEmpty extends MessageMedia{}
 public static class Message{public int id,ttl;public boolean noforwards;public String attachPath="";public MessageMedia media;public ArrayList<Object> restriction_reason=new ArrayList<>();public ArrayList<MessageEntity> entities=new ArrayList<>();}}
''')
 put('org/telegram/messenger/MessageObject.java',r'''package org.telegram.messenger;import org.telegram.tgnet.TLRPC;public class MessageObject{
 public static final int TYPE_TEXT=0;public int type,currentAccount;public long dialog=7,group;public boolean sponsored,ephemeral;public TLRPC.Message messageOwner=new TLRPC.Message();
 public boolean isSponsored(){return sponsored;}public boolean isEphemeral(){return ephemeral;}public long getGroupIdForUse(){return group;}public long getDialogId(){return dialog;}public int getId(){return messageOwner.id;}}
''')
 put('org/telegram/ui/Cells/ChatMessageCell.java',r'''package org.telegram.ui.Cells;import android.view.*;import android.content.*;import android.graphics.*;import org.telegram.messenger.MessageObject;
 public class ChatMessageCell extends View{public boolean drawForSignatureExport;public MessageObject message;public int left=10,top=10,right=210,bottom=90;public static class TransitionParams{public float animateChangeProgress=1;}private TransitionParams transition=new TransitionParams();
 public ChatMessageCell(Context c){super(c);}public MessageObject getMessageObject(){return message;}public TransitionParams getTransitionParams(){return transition;}
 public Object getCurrentBackgroundDrawable(boolean update){return message==null?null:this;}public int getBackgroundDrawableLeft(){return left;}public int getBackgroundDrawableRight(){return right;}public int getBackgroundDrawableTop(){return top;}public int getBackgroundDrawableBottom(){return bottom;}
 public boolean parentBackground;public int parentPasses,outboundsPasses;
 public boolean drawBackgroundInParent(){return parentBackground;}public boolean hasOutboundsContent(){return true;}
 public void drawBackgroundInternal(Canvas c,boolean parent){parentPasses++;Paint p=new Paint();p.setColor(0xff2589c0);c.drawRoundRect(left,top,right,bottom,20,20,p);}
 public void drawOutboundsContent(Canvas c){outboundsPasses++;}
 @Override protected void onDraw(Canvas c){int save=c.save();c.translate(0,getPaddingTop());if(!parentBackground)drawBackgroundInternal(c,false);Paint p=new Paint();p.setColor(Color.WHITE);p.setTextSize(20);c.drawText("Native painter DOUBLE",20,50,p);c.restoreToCount(save);}}
''')
 put('org/telegram/messenger/NotificationCenter.java',r'''package org.telegram.messenger;import java.util.*;public class NotificationCenter{
 public interface NotificationCenterDelegate{void didReceivedNotification(int id,int account,Object...args);}public static final int didReceiveNewMessages=1,messageReceivedByServer=2,messageSendError=3;
 private static final NotificationCenter[] accounts={new NotificationCenter(0),new NotificationCenter(1)};private final int account;private final Map<Integer,ArrayList<NotificationCenterDelegate>> listeners=new HashMap<>();private NotificationCenter(int a){account=a;}
 public static NotificationCenter getInstance(int a){return accounts[a];}public void addObserver(NotificationCenterDelegate l,int id){listeners.computeIfAbsent(id,k->new ArrayList<>()).add(l);}public void removeObserver(NotificationCenterDelegate l,int id){listeners.computeIfAbsent(id,k->new ArrayList<>()).remove(l);}public int count(){int n=0;for(var x:listeners.values())n+=x.size();return n;}
 public void postNotificationName(int id,Object...args){for(var l:new ArrayList<>(listeners.getOrDefault(id,new ArrayList<>())))l.didReceivedNotification(id,account,args);}}
''')
 put('org/telegram/messenger/SendMessagesHelper.java',r'''package org.telegram.messenger;import org.telegram.tgnet.TLRPC;public class SendMessagesHelper{public static class SendMessageParams{public TLRPC.TL_document document;public String path;public long peer;public int scheduleDate;}
 public static int sends;public static java.util.function.Consumer<SendMessageParams> onSend;private static final SendMessagesHelper instance=new SendMessagesHelper();public static SendMessagesHelper getInstance(int a){return instance;}public void sendMessage(SendMessageParams p){sends++;if(onSend!=null)onSend.accept(p);}}
''')
 put('org/telegram/messenger/AndroidUtilities.java',r'''package org.telegram.messenger;import android.os.*;public class AndroidUtilities{private static final Handler ui=new Handler(Looper.getMainLooper());public static void runOnUIThread(Runnable r){ui.post(r);}public static void runOnUIThread(Runnable r,long t){ui.postDelayed(r,t);}public static void cancelRunOnUIThread(Runnable r){ui.removeCallbacks(r);}}
''')
 put('org/telegram/messenger/Utilities.java',r'''package org.telegram.messenger;public class Utilities{public static class Queue{public void postRunnable(Runnable r){new Thread(r).start();}}public static final Queue globalQueue=new Queue();}
''')
 put('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}')
 put('org/telegram/ui/ActionBar/BaseFragment.java',r'''package org.telegram.ui.ActionBar;public class BaseFragment{public android.app.Activity activity;public android.content.Intent lastIntent;public int request;public android.app.Activity getParentActivity(){return activity;}public void startActivityForResult(android.content.Intent i,int r){lastIntent=i;request=r;}}
''')
