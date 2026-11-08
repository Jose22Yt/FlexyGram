#!/usr/bin/env python3
"""Real lyrics RecyclerView, parser and clock with explicit playback/provider doubles, no APK."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('music_pipeline',HERE.parent/'music_visual/run.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
spec=importlib.util.spec_from_file_location('music_stubs',HERE.parent/'music_visual/stubs.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def write_stubs(source,root):
 base.write_stubs(source,root)
 def put(path,text):
  p=source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 player=root/'TMessagesProj/src/main/java/app/exteraless/player'
 for name in ('LyricsView','Lyrics','LyricsFill'):
  put('app/exteraless/player/'+name+'.java',(player/(name+'.java')).read_text())
 import re
 r=source/'org/telegram/messenger/R.java';text=r.read_text();names=sorted(set(re.findall(r'R.string.(\w+)',(player/'LyricsView.java').read_text()))-set(re.findall(r'int (\w+)=',text)))
 text=text.replace('public static class string {','public static class string {'+''.join('public static final int '+n+'='+str(1000+i)+';' for i,n in enumerate(names)));r.write_text(text)
 put('tw/nekomimi/nekogram/helpers/TypefaceHelper.java','package tw.nekomimi.nekogram.helpers;public class TypefaceHelper{public static android.graphics.Typeface lyricsTypeface(){return android.graphics.Typeface.create("sans-serif",1);}}')
 put('org/telegram/ui/Components/RadialProgressView.java','package org.telegram.ui.Components;public class RadialProgressView extends android.view.View{public RadialProgressView(android.content.Context c){super(c);}public void setSize(int v){}public void setProgressColor(int c){}}')
 put('org/telegram/ui/Components/RecyclerListView.java','''package org.telegram.ui.Components;import android.content.*;import android.view.*;import androidx.recyclerview.widget.RecyclerView;public class RecyclerListView extends RecyclerView{
 public java.util.ArrayList<RecyclerView.OnScrollListener> listeners=new java.util.ArrayList<>();public void addOnScrollListener(RecyclerView.OnScrollListener listener){super.addOnScrollListener(listener);listeners.add(listener);}public void simulateScrollState(int state){for(var l:listeners)l.onScrollStateChanged(this,state);}
 public RecyclerListView(Context c){super(c);}public void setSelectorDrawableColor(int color){}
 public interface OnItemClickListener{void onItemClick(View v,int position);}public OnItemClickListener click;public void setOnItemClickListener(OnItemClickListener l){click=l;}
 public static class Holder extends RecyclerView.ViewHolder{public Holder(View v){super(v);}}
 public abstract static class SelectionAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder>{public abstract boolean isEnabled(RecyclerView.ViewHolder h);}}
 ''')
 put('androidx/recyclerview/R.java','''package androidx.recyclerview;
public final class R {
 public static final class attr {
  public static final int alpha = 0x7f040000;
  public static final int fastScrollEnabled = 0x7f040001;
  public static final int fastScrollHorizontalThumbDrawable = 0x7f040002;
  public static final int fastScrollHorizontalTrackDrawable = 0x7f040003;
  public static final int fastScrollVerticalThumbDrawable = 0x7f040004;
  public static final int fastScrollVerticalTrackDrawable = 0x7f040005;
  public static final int layoutManager = 0x7f040006;
  public static final int recyclerViewStyle = 0x7f040007;
  public static final int reverseLayout = 0x7f040008;
  public static final int spanCount = 0x7f040009;
  public static final int stackFromEnd = 0x7f04000a;
 }
 public static final class dimen {
  public static final int fastscroll_default_thickness = 0x7f070001;
  public static final int fastscroll_margin = 0x7f070002;
  public static final int fastscroll_minimum_range = 0x7f070003;
  public static final int item_touch_helper_max_drag_scroll_per_frame = 0x7f070004;
  public static final int item_touch_helper_swipe_escape_max_velocity = 0x7f070005;
  public static final int item_touch_helper_swipe_escape_velocity = 0x7f070006;
 }
 public static final class id {
  public static final int item_touch_helper_previous_elevation = 0x7f090001;
 }
 public static final class styleable {
  public static final int[] RecyclerView = new int[] {
   android.R.attr.orientation,
   android.R.attr.clipToPadding,
   android.R.attr.descendantFocusability,
   0x7f040001, 0x7f040002, 0x7f040003, 0x7f040004, 0x7f040005,
   0x7f040006, 0x7f040008, 0x7f040009, 0x7f04000a
  };
  public static final int RecyclerView_android_orientation = 0;
  public static final int RecyclerView_android_clipToPadding = 1;
  public static final int RecyclerView_android_descendantFocusability = 2;
  public static final int RecyclerView_fastScrollEnabled = 3;
  public static final int RecyclerView_fastScrollHorizontalThumbDrawable = 4;
  public static final int RecyclerView_fastScrollHorizontalTrackDrawable = 5;
  public static final int RecyclerView_fastScrollVerticalThumbDrawable = 6;
  public static final int RecyclerView_fastScrollVerticalTrackDrawable = 7;
  public static final int RecyclerView_layoutManager = 8;
  public static final int RecyclerView_reverseLayout = 9;
  public static final int RecyclerView_spanCount = 10;
  public static final int RecyclerView_stackFromEnd = 11;
 }
}''')
 put('androidx/customview/poolingcontainer/R.java','package androidx.customview.poolingcontainer;public final class R{public static final class id{public static final int is_pooling_container_tag=0x7f090010;public static final int pooling_container_listener_holder_tag=0x7f090011;}}')
 put('androidx/customview/R.java','package androidx.customview;public final class R{public static final class id{public static final int tag_unhandled_key_event_manager=0x7f090020;public static final int tag_unhandled_key_listeners=0x7f090021;}}')
 put('androidx/core/R.java','''package androidx.core;
public final class R {
 public static final class attr {}
 public static final class styleable {}
 public static final class id {
  public static final int accessibility_action_clickable_span = 0x7f090001;
  public static final int accessibility_custom_action_0 = 0x7f090002;
  public static final int accessibility_custom_action_1 = 0x7f090003;
  public static final int accessibility_custom_action_2 = 0x7f090004;
  public static final int accessibility_custom_action_3 = 0x7f090005;
  public static final int accessibility_custom_action_4 = 0x7f090006;
  public static final int accessibility_custom_action_5 = 0x7f090007;
  public static final int accessibility_custom_action_6 = 0x7f090008;
  public static final int accessibility_custom_action_7 = 0x7f090009;
  public static final int accessibility_custom_action_8 = 0x7f09000a;
  public static final int accessibility_custom_action_9 = 0x7f09000b;
  public static final int accessibility_custom_action_10 = 0x7f09000c;
  public static final int accessibility_custom_action_11 = 0x7f09000d;
  public static final int accessibility_custom_action_12 = 0x7f09000e;
  public static final int accessibility_custom_action_13 = 0x7f09000f;
  public static final int accessibility_custom_action_14 = 0x7f090010;
  public static final int accessibility_custom_action_15 = 0x7f090011;
  public static final int accessibility_custom_action_16 = 0x7f090012;
  public static final int accessibility_custom_action_17 = 0x7f090013;
  public static final int accessibility_custom_action_18 = 0x7f090014;
  public static final int accessibility_custom_action_19 = 0x7f090015;
  public static final int accessibility_custom_action_20 = 0x7f090016;
  public static final int accessibility_custom_action_21 = 0x7f090017;
  public static final int accessibility_custom_action_22 = 0x7f090018;
  public static final int accessibility_custom_action_23 = 0x7f090019;
  public static final int accessibility_custom_action_24 = 0x7f09001a;
  public static final int accessibility_custom_action_25 = 0x7f09001b;
  public static final int accessibility_custom_action_26 = 0x7f09001c;
  public static final int accessibility_custom_action_27 = 0x7f09001d;
  public static final int accessibility_custom_action_28 = 0x7f09001e;
  public static final int accessibility_custom_action_29 = 0x7f09001f;
  public static final int accessibility_custom_action_30 = 0x7f090020;
  public static final int accessibility_custom_action_31 = 0x7f090021;
  public static final int tag_accessibility_actions = 0x7f090022;
  public static final int tag_accessibility_clickable_spans = 0x7f090023;
  public static final int tag_accessibility_heading = 0x7f090024;
  public static final int tag_accessibility_pane_title = 0x7f090025;
  public static final int tag_screen_reader_focusable = 0x7f090026;
  public static final int tag_state_description = 0x7f090027;
  public static final int tag_unhandled_key_event_ids = 0x7f090028;
  public static final int tag_unhandled_key_event_manager = 0x7f090029;
  public static final int tag_unhandled_key_listeners = 0x7f09002a;
  public static final int tag_window_insets_animation_callback = 0x7f09002b;
  public static final int tag_on_apply_window_listener = 0x7f09002c;
  public static final int tag_on_receive_content_listener = 0x7f09002d;
  public static final int tag_on_receive_content_mime_types = 0x7f09002e;
  public static final int view_tree_lifecycle_owner = 0x7f09002f;
  public static final int view_tree_view_model_store_owner = 0x7f090030;
  public static final int view_tree_saved_state_registry_owner = 0x7f090031;
  public static final int item_touch_helper_previous_elevation = 0x7f090032;
 }
}''')
 # Music layout fixtures are not needed in the lyrics suite.
 (source/'app/exteraless/player/LayoutFixture.java').unlink()
if __name__=='__main__':raise SystemExit(pipeline.main(here=HERE,test_class='LyricsUiTest',stubs_writer=write_stubs,extra_aars=[('androidx.recyclerview','recyclerview','1.4.0'),('androidx.customview','customview','1.2.0'),('androidx.customview','customview-poolingcontainer','1.0.0')]))
