"""Execute the real Bubble editor row factory/classifiers; Android layout APIs are explicit doubles."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_bubble_controls_fill_native_group_and_preview_is_an_independent_row(tmp_path):
    bubbles=(JAVA/'app/flexygram/bubbles/BubbleSettingsActivity.java').read_text()
    native=(JAVA/'tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java').read_text()
    matte=(JAVA/'app/flexygram/settings/SignatureMatteSettingsActivity.java').read_text()
    adapter=bubbles[bubbles.index('private final class Adapter'):]
    source='''import java.util.*;
public class Probe {
 static final int SLIDER=110,PREVIEW=111;
 static final int TYPE_SHADOW=1,TYPE_SETTINGS=2,TYPE_CHECK=3,TYPE_HEADER=4,TYPE_NOTIFICATION_CHECK=5,TYPE_DETAIL_SETTINGS=6,TYPE_INFO_PRIVACY=7,TYPE_TEXT=8,TYPE_CHECKBOX=9,TYPE_RADIO=10,TYPE_ACCOUNT=11,TYPE_EMOJI=12,TYPE_EMOJI_SELECTION=13,TYPE_CREATION=14,TYPE_FLICKER=15,TYPE_CHECK2=16,TYPE_CHECKBOX2=17;
 static int dp(int v){return v;}
 static class Context{}
 static class View{
  ViewGroup.LayoutParams params;Object tag;final Context context;View(Context c){context=c;}
  Context getContext(){return context;}void setLayoutParams(ViewGroup.LayoutParams p){params=p;}void setTag(Object v){tag=v;}
 }
 static class ViewGroup extends View{
  ViewGroup(Context c){super(c);}static class LayoutParams{static final int MATCH_PARENT=-1,WRAP_CONTENT=-2;int width,height;LayoutParams(int w,int h){width=w;height=h;}}
 }
 static class RecyclerView{static class LayoutParams extends ViewGroup.LayoutParams{int leftMargin,topMargin,rightMargin,bottomMargin;LayoutParams(int w,int h){super(w,h);}void setMargins(int l,int t,int r,int b){leftMargin=l;topMargin=t;rightMargin=r;bottomMargin=b;}}static class ViewHolder{View itemView;ViewHolder(View v){itemView=v;}}}
 static class RecyclerListView{static final int TAG_NOT_SECTION=12;static class Holder extends RecyclerView.ViewHolder{Holder(View v){super(v);}}}
 static class BubblePreviewView extends View{BubblePreviewView(Context c,Object wallpaper){super(c);}}
 static class TransparencyCell extends View{TransparencyCell(Context c){super(c);}}
 static class BubbleConfig{static boolean outline;static int style,fusion;static void load(){}static boolean outlineEnabled(){return outline;}static int outlineStyle(){return style;}static int fusionMode(){return fusion;}}
 static class app{static class exteraless{static class appearance{static class AppearanceConfig{static boolean separateHeaders(){return true;}}}}}
 static class NativeAdapter{
  boolean isSettings3Embedded(){return false;}boolean isSignatureSettingsPage(){return false;}
  NATIVE_CLASSIFIER
  SHARED_CLASSIFIER
  public int getItemViewType(int position){return TYPE_SETTINGS;}
  public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){View v=new View(parent.getContext());v.setLayoutParams(new RecyclerView.LayoutParams(-1,-2));return new RecyclerListView.Holder(v);}
 }
 static class MatteAdapter extends NativeAdapter{MATTE_CLASSIFIER}
 static class ListView{boolean animatorConfigured;Object animator=new Object();void setItemAnimator(Object value){animatorConfigured=true;animator=value;}}
 static class BasePage{
  int rowCount;final ListView listView=new ListView();void updateRows(){rowCount=0;}int addRow(){return rowCount++;}int addRow(String key){return addRow();}
  public View createView(Context c){return new View(c);}
 }
 static class Page extends BasePage{
  int transparencyRow,borderRow,previewRow,positionRow,blurRow,enabledRow,fuseRow,styleRow,pearlRow,fusionIntensityRow,fusionAdaptRow;
  Object contextualWallpaper;BubblePreviewView preview;
  UPDATE_ROWS
  CREATE_VIEW
  class Adapter extends MatteAdapter{
   ADAPTER_TYPE
   ADAPTER_CLASSIFIER
   FACTORY
  }
 }
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
  Context context=new Context();ViewGroup parent=new ViewGroup(context);
  for(boolean outline:new boolean[]{false,true})for(int style=0;style<4;style++)for(int fusion=0;fusion<3;fusion++){
   BubbleConfig.outline=outline;BubbleConfig.style=style;BubbleConfig.fusion=fusion;
   Page page=new Page();page.updateRows();page.createView(context);Page.Adapter adapter=page.new Adapter();
   check(page.listView.animatorConfigured&&page.listView.animator==null);
   check(!adapter.isSettingsContentType(PREVIEW)&&adapter.isSettingsContentType(SLIDER));
   // The first control gets the group's large top corners rather than connecting to the wallpaper.
   check(!adapter.isSettingsContentType(adapter.getItemViewType(page.transparencyRow-1)));
   for(int position=0;position<page.rowCount;position++){
    int type=adapter.getItemViewType(position);View view=adapter.onCreateViewHolder(parent,type).itemView;
    check(view.params!=null&&view.params.width==-1&&view.params.height==-2);
    if(position==page.previewRow){
     check(view instanceof BubblePreviewView&&Objects.equals(view.tag,RecyclerListView.TAG_NOT_SECTION));
     RecyclerView.LayoutParams p=(RecyclerView.LayoutParams)view.params;
     check(p.leftMargin+8==12&&p.rightMargin+8==12&&p.topMargin>=0&&p.bottomMargin>0);
    }else{
     check(adapter.isSettingsContentType(type));
     if(type==SLIDER)check(view instanceof TransparencyCell);
    }
   }
   check(page.rowCount==(outline?(style==0?8:9)+(fusion==2?2:0):4));
  }
 }
}'''
    parts={
      'NATIVE_CLASSIFIER':method(native,'protected boolean isSectionContent(int viewType)'),
      'SHARED_CLASSIFIER':method(native,'public boolean isSettingsContentType(int type)'),
      'MATTE_CLASSIFIER':method(matte,'protected boolean isSectionContent(int type)'),
      'UPDATE_ROWS':method(bubbles,'protected void updateRows()'),
      'CREATE_VIEW':method(bubbles,'public View createView(Context context)'),
      'ADAPTER_TYPE':method(adapter,'public int getItemViewType(int position)'),
      'ADAPTER_CLASSIFIER':method(adapter,'protected boolean isSectionContent(int type)'),
      'FACTORY':method(adapter,'public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int type)'),
    }
    for key,body in parts.items():source=source.replace(key,body)
    probe(tmp_path,{'Probe.java':source})
