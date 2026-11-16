"""Execute the Native Test selector branches; Android row binding hosts are explicit doubles."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe
from test_native_baseline import NATIVE


def test_clean_selector_has_exactly_three_radio_choices_and_no_effect_work(tmp_path):
    page=(JAVA/'app/flexygram/bubbles/BubbleSettingsActivity.java').read_text()
    gate='if (org.telegram.messenger.BuildConfig.NATIVE_BASELINE_TEST)'
    rows=method(method(page,'protected void updateRows()'),gate)
    click=method(method(page,'protected void onItemClick('),gate)
    bind=method(method(page,'public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial)'),gate)
    probe(tmp_path,{
        'org/telegram/messenger/BuildConfig.java':NATIVE,
        'Probe.java':'''import java.util.*;
public class Probe{
 static class BubbleConfig{static final int TELEGRAM=0,FLEXYGRAM=1,IPHONE=2;static boolean small;static boolean smallTimestamps(){return small;}static void setSmallTimestamps(boolean v){small=v;writes++;}static int shape,writes;static int shape(){return shape;}static void setShape(int v){if(v<0||v>2)throw new AssertionError();shape=v;writes++;}}
 static class R{static class string{static final int FlexyBubbleShapeTelegram=101,FlexyBubbleShapeFlexyGram=102,FlexyBubbleShapeIos27=103,FlexyBubbleSmallTimestamp=104;}}
 static class TextRadioCell{String text;boolean checked,divider;void setTextAndCheck(String s,boolean c,boolean d){text=s;checked=c;divider=d;}}
 static class TextCheckCell extends TextRadioCell{}
 static class RecyclerView{static class ViewHolder{Object itemView=new TextRadioCell();}}
 static class Adapter{int changes;void notifyDataSetChanged(){changes++;}void notifyItemChanged(int p){changes++;}}
 int timestampRow;final List<String> keys=new ArrayList<>();final Adapter listAdapter=new Adapter();int addRow(String k){keys.add(k);return keys.size()-1;}
 static String getString(int id){return Integer.toString(id);}
 void rows(){ROWS}
 void click(int position){if(position<0)return;CLICK}
 void bind(RecyclerView.ViewHolder holder,int position){BIND}
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();p.rows();check(p.keys.equals(Arrays.asList("flexyBubbleShapeTelegram","flexyBubbleShapeFlexyGram","flexyBubbleShapeIPhone","flexyBubbleSmallTimestamp")));
  for(int choice=0;choice<3;choice++){
   p.click(choice);check(BubbleConfig.shape()==choice);
   int writes=BubbleConfig.writes,updates=p.listAdapter.changes;
   p.click(choice);p.click(-1);p.click(4);p.click(99);check(writes==BubbleConfig.writes&&updates==p.listAdapter.changes);
   int checked=0;
   for(int row=0;row<3;row++){
    RecyclerView.ViewHolder h=new RecyclerView.ViewHolder();p.bind(h,row);TextRadioCell cell=(TextRadioCell)h.itemView;
    check(cell.text.equals(Integer.toString(101+row))&&cell.divider);
    check(cell.checked==(row==choice));if(cell.checked)checked++;
   }
   check(checked==1);
   boolean old=BubbleConfig.small;p.click(3);check(BubbleConfig.small!=old);
   RecyclerView.ViewHolder toggle=new RecyclerView.ViewHolder();toggle.itemView=new TextCheckCell();p.bind(toggle,3);check(((TextCheckCell)toggle.itemView).checked==BubbleConfig.small);
  }
 }
}'''.replace('ROWS',rows).replace('CLICK',click).replace('BIND',bind)
    })


def test_clean_shape_settings_are_reachable_but_retired_features_stay_hidden():
    registry=(JAVA/'app/flexygram/settings/signature/SignatureSettingsRegistry.java').read_text()
    visible=method(registry,'public static boolean visible(String id)')
    assert '"bubbles"' not in visible
    for retired in ['studio','flexyfiles','context','bottom_tabs','glare','app_navigation']:
        assert '"'+retired+'"' in visible
    direct=(JAVA/'app/flexygram/settings/signature/SignatureDirectSettingsActivity.java').read_text()
    links=method(direct,'private void links(')
    assert '"bubble_style"' not in links
    for retired in ['delete_motion','context','navigationEditor']:
        assert '"'+retired+'"' in links


def test_shape_refresh_invalidates_visible_cells_only_after_a_real_change(tmp_path):
    chat=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    body=method(chat,'private void refreshCleanBubbleShape()')
    assert 'BubbleConfig.load();\n        refreshCleanBubbleShape();' in chat
    probe(tmp_path,{
        'org/telegram/messenger/BuildConfig.java':NATIVE,
        'app/flexygram/bubbles/BubbleConfig.java':'package app.flexygram.bubbles;public class BubbleConfig{public static int value;public static boolean small;public static boolean smallTimestamps(){return small;}public static int shape(){return value;}}',
        'Probe.java':'''public class Probe{
 int lastResumedBubbleShape=-1;boolean lastResumedSmallTimestamp;static class Adapter{int rebinds;void notifyDataSetChanged(){rebinds++;}}static class ListView{int invalidations;Adapter adapter=new Adapter();Adapter getAdapter(){return adapter;}void invalidateViews(){invalidations++;}}
 ListView chatListView=new ListView();
 BODY
 public static void main(String[]args){Probe p=new Probe();p.refreshCleanBubbleShape();
 for(int i=0;i<10000;i++)p.refreshCleanBubbleShape();if(p.chatListView.invalidations!=0)throw new AssertionError("repeated resume work");
 app.flexygram.bubbles.BubbleConfig.value=2;p.refreshCleanBubbleShape();if(p.chatListView.invalidations!=1)throw new AssertionError("stale visible rows");
 p.refreshCleanBubbleShape();if(p.chatListView.invalidations!=1)throw new AssertionError();
 app.flexygram.bubbles.BubbleConfig.small=true;p.refreshCleanBubbleShape();if(p.chatListView.adapter.rebinds!=1)throw new AssertionError("timestamp not remeasured");
 for(int i=0;i<10000;i++)p.refreshCleanBubbleShape();if(p.chatListView.adapter.rebinds!=1)throw new AssertionError("repeated remeasure");
 p.chatListView=null;app.flexygram.bubbles.BubbleConfig.value=1;p.refreshCleanBubbleShape();if(p.lastResumedBubbleShape!=1)throw new AssertionError();
 }}'''.replace('BODY',body)
    })
