"""Execute production deletion ownership methods with explicit row/model host doubles."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2]
def method(source,anchor):
    start=source.index(anchor);end=source.index('{',start)+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]
class BetaDeleteRoute(unittest.TestCase):
    def test_only_marked_native_deletions_are_consumed_once_without_recycled_or_scheduled_rows(self):
        s=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/recyclerview/ChatListItemAnimator.java').read_text()
        methods=method(s,'    public void prepareFlexyDelete(')+method(s,'    private boolean takeFlexyDelete(')
        chat=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java').read_text()
        visible=method(chat,'                            for (int childIndex = 0; childIndex < chatListView.getChildCount(); childIndex++)')
        code='''public class DeleteRouteProbe {
        static class MessageObject {boolean deleted=true,scheduledSent;}
        static class View {}
        static class ChatMessageCell extends View {MessageObject message=new MessageObject();Object group;MessageObject getMessageObject(){return message;}Object getCurrentMessagesGroup(){return group;}}
        static class RecyclerView {static class ViewHolder {Object itemView;ViewHolder(Object v){itemView=v;}}}
        static class ListHost {
         java.util.ArrayList<View> children=new java.util.ArrayList<>();Object getContext(){return null;}
         int getChildCount(){return children.size();}View getChildAt(int i){return children.get(i);}
         RecyclerView.ViewHolder getChildViewHolder(View v){return new RecyclerView.ViewHolder(v);}
        }ListHost recyclerListView=new ListHost(),chatListView=recyclerListView;
        DeleteRouteProbe chatListItemAnimator=this;
        final java.util.Set<MessageObject> flexyPendingDeletes=java.util.Collections.newSetFromMap(new java.util.WeakHashMap<>());
        '''+methods+'void markVisible(MessageObject obj){'+visible+'}'+'''
        static void check(boolean value){if(!value)throw new AssertionError();}
        public static void main(String[] args){
          DeleteRouteProbe owner=new DeleteRouteProbe();ChatMessageCell cell=new ChatMessageCell();
          check(!owner.takeFlexyDelete(cell)); // Filtering an unmarked row is native.
          owner.prepareFlexyDelete(new RecyclerView.ViewHolder(cell));check(owner.takeFlexyDelete(cell));check(!owner.takeFlexyDelete(cell));
          owner.prepareFlexyDelete(new RecyclerView.ViewHolder(cell));MessageObject original=cell.message;cell.message=new MessageObject();check(!owner.takeFlexyDelete(cell));cell.message=original;check(owner.takeFlexyDelete(cell));
          cell.message.scheduledSent=true;owner.prepareFlexyDelete(new RecyclerView.ViewHolder(cell));check(!owner.takeFlexyDelete(cell));cell.message.scheduledSent=false;
          cell.group=new Object();owner.prepareFlexyDelete(new RecyclerView.ViewHolder(cell));check(!owner.takeFlexyDelete(cell));cell.group=null;
          cell.message.deleted=false;owner.prepareFlexyDelete(new RecyclerView.ViewHolder(cell));check(!owner.takeFlexyDelete(cell));
          owner.prepareFlexyDelete(null);owner.prepareFlexyDelete(new RecyclerView.ViewHolder(new Object()));
          check(owner.flexyPendingDeletes.isEmpty());
          ChatMessageCell first=new ChatMessageCell(),second=new ChatMessageCell();
          owner.chatListView.children.add(first);owner.chatListView.children.add(second);
          owner.markVisible(second.message);check(!owner.takeFlexyDelete(first));check(owner.takeFlexyDelete(second));
          owner.markVisible(first.message);check(owner.takeFlexyDelete(first));
          System.out.println("PASS native deletion ownership, one-shot, recycle, groups and scheduled fallback");
        }}'''
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);(folder/'DeleteRouteProbe.java').write_text(code)
            stub=folder/'app/flexygram/bubbles/deletion/DeleteMotionSettings.java';stub.parent.mkdir(parents=True);stub.write_text('package app.flexygram.bubbles.deletion;public class DeleteMotionSettings{public static int get(Object c){return 1;}}')
            subprocess.run(['javac','-d',str(folder),str(folder/'DeleteRouteProbe.java'),str(stub)],check=True,capture_output=True)
            r=subprocess.run(['java','-cp',str(folder),'DeleteRouteProbe'],check=True,capture_output=True,text=True)
            self.assertIn('PASS native deletion ownership',r.stdout)
