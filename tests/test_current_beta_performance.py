"""Production section rendering: pooling, nested callbacks and geometry. No device/FPS claims."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_sections_keep_outer_geometry_during_nested_draw_and_recover_after_callback_failure(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/RecyclerListView.java').read_text()
    drawer=method(source,'public static class SectionsDrawer')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
public class Probe {
 static int dp(float v){return Math.round(v);}
 static float lerp(float a,float b,float t){return a+(b-a)*t;}
 static class Utilities{interface Callback5<A,B,C,D,E>{void run(A a,B b,C c,D d,E e);}}
 DRAWER
 static List<SectionsDrawer.Section> rows(){return new ArrayList<>(List.of(
  new SectionsDrawer.Section(0,40,1),new SectionsDrawer.Section(100,140,1),new SectionsDrawer.Section(200,240,.5f)));}
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
  List<float[]> actual=new ArrayList<>();boolean[] nested={false};
  SectionsDrawer.draw(rows(),28,(a,b,t,d,x)->{
   actual.add(new float[]{a,b,t,d,x});
   if(!nested[0]){nested[0]=true;SectionsDrawer.draw(new ArrayList<>(List.of(new SectionsDrawer.Section(900,960,1))),12,(aa,bb,tt,dd,xx)->check(aa==900&&bb==960));}
  });
  check(actual.size()==3);check(actual.get(0)[0]==0&&actual.get(1)[0]==100&&actual.get(2)[0]==200&&actual.get(2)[4]==.5f);
  try{SectionsDrawer.draw(rows(),28,(a,b,t,d,x)->{throw new IllegalStateException("test callback");});throw new AssertionError();}catch(IllegalStateException expected){}
  actual.clear();SectionsDrawer.draw(rows(),28,(a,b,t,d,x)->actual.add(new float[]{a,b,t,d,x}));check(actual.size()==3);
  var unsorted=rows();Collections.reverse(unsorted);actual.clear();SectionsDrawer.draw(unsorted,28,(a,b,t,d,x)->actual.add(new float[]{a,b,t,d,x}));
  check(actual.size()==3&&actual.get(0)[0]==0&&actual.get(2)[0]==200);
  // A second warm draw reuses the actual float buffers. This cache contains only numeric geometry.
  var state=SectionsDrawer.drawStates.get();var first=state.pool.get(0);int count=state.pool.size();
  for(int i=0;i<10000;i++)SectionsDrawer.draw(rows(),28,(a,b,t,d,x)->{});
  check(state.pool.size()==count&&state.pool.get(0)==first&&!state.inUse&&state.groups.isEmpty());
  check(state.nested!=null&&!state.nested.inUse&&state.nested.groups.isEmpty());
  List<SectionsDrawer.Section> large=new ArrayList<>();for(int i=0;i<200;i++)large.add(new SectionsDrawer.Section(i*100,i*100+40,1));
  int[] drawn={0};SectionsDrawer.draw(large,28,(a,b,t,d,x)->drawn[0]++);check(drawn[0]==200&&state.pool.size()==128&&state.groups.isEmpty());
 }
}'''.replace('DRAWER',drawer)})


def test_animation_section_pool_updates_geometry_without_retaining_old_rows(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/RecyclerListView.java').read_text()
    drawer=method(source,'public static class SectionsDrawer')
    obtain=method(source,'private SectionsDrawer.Section obtainAnimatedSection(')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
public class Probe {
 static int dp(float v){return Math.round(v);}static float lerp(float a,float b,float t){return a+(b-a)*t;}
 static class Utilities{interface Callback5<A,B,C,D,E>{void run(A a,B b,C c,D d,E e);}}
 DRAWER
 private ArrayList<SectionsDrawer.Section> sectionPool;
 OBTAIN
 public static void main(String[]args){
  Probe list=new Probe();var first=list.obtainAnimatedSection(0,0,40,1,false);var second=list.obtainAnimatedSection(1,44,84,1,false);
  for(int frame=1;frame<10000;frame++){
   var row=list.obtainAnimatedSection(0,frame,frame+40,.25f,true);
   if(row!=first||row.from!=frame||row.to!=frame+40||row.alpha!=.25f||!row.round)throw new AssertionError();
   if(list.obtainAnimatedSection(1,44,84,1,false)!=second)throw new AssertionError();
  }
  if(list.sectionPool.size()!=2)throw new AssertionError("pool grew without more visible children");
  for(int i=2;i<200;i++){var row=list.obtainAnimatedSection(i,i,i+1,1,false);if(row.from!=i)throw new AssertionError("overflow geometry");}
  if(list.sectionPool.size()!=128)throw new AssertionError("unbounded pool");
 }
}'''.replace('DRAWER',drawer).replace('OBTAIN',obtain)})
