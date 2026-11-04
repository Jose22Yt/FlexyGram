"""Execute actual native section geometry. These checks do not compile/package the APK."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_native_segmented_geometry_keeps_group_edges_and_existing_default_path(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/RecyclerListView.java').read_text()
    drawer=method(source,'public static class SectionsDrawer')
    probe(tmp_path, {'Probe.java': '''
import java.util.*;
public class Probe {
 static int dp(float n){return Math.round(n);}
 static float lerp(float a,float b,float t){return a+(b-a)*t;}
 static class Utilities {interface Callback5<A,B,C,D,E>{void run(A a,B b,C c,D d,E e);}}
 DRAWER
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  List<SectionsDrawer.Section> sections=new ArrayList<>(List.of(
   new SectionsDrawer.Section(0,48,1),new SectionsDrawer.Section(52,100,1),new SectionsDrawer.Section(104,152,1),
   new SectionsDrawer.Section(180,228,1),new SectionsDrawer.Section(232,280,1),
   new SectionsDrawer.Section(320,368,1)));
  List<float[]> shape=new ArrayList<>();SectionsDrawer.draw(sections,28,(a,b,t,d,x)->shape.add(new float[]{a,b,t,d,x}),true,6,4);
  check(shape.size()==6);
  float[][] expected={{28,6},{6,6},{6,28},{28,6},{6,28},{28,28}};
  for(int i=0;i<expected.length;i++)check(shape.get(i)[2]==expected[i][0]&&shape.get(i)[3]==expected[i][1]);
  sections.get(1).alpha=.3f;shape.clear();SectionsDrawer.draw(sections,28,(a,b,t,d,x)->shape.add(new float[]{a,b,t,d,x}),true,6,4);
  check(shape.get(1)[4]==.3f&&shape.get(1)[2]==6&&shape.get(1)[3]==6);
  // The existing non-settings overload retains 2dp spacing and 4dp inner corners.
  sections=new ArrayList<>(List.of(new SectionsDrawer.Section(0,48,1),new SectionsDrawer.Section(50,98,1)));
  shape.clear();SectionsDrawer.draw(sections,20,(a,b,t,d,x)->shape.add(new float[]{a,b,t,d,x}),true);
  check(shape.size()==2&&shape.get(0)[3]==4&&shape.get(1)[2]==4);
 }
}'''.replace('DRAWER',drawer)})


def test_settings_surface_remains_distinct_in_dark_light_and_matching_custom_themes(tmp_path):
    probe(tmp_path, {'Probe.java': '''
import app.flexygram.settings.signature.SettingsCardStyle;
public class Probe {
 public static void main(String[] args){
  for(int page:new int[]{0xff151f28,0xff000000,0xffeeeeee,0xffffffff}){
   int card=SettingsCardStyle.surface(page,page);
   if(card==page||(card>>>24)!=255)throw new AssertionError("card disappeared into page");
  }
  if(SettingsCardStyle.surface(0xff22313f,0xff151f28)!=0xff22313f)throw new AssertionError("unnecessary palette change");
  if(SettingsCardStyle.ICON!=24||SettingsCardStyle.GAP!=4)throw new AssertionError("compact sizing");
 }
}'''}, [JAVA/'app/flexygram/settings/signature/SettingsCardStyle.java'])
