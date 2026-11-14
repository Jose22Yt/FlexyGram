"""Exercise the real application resource wrapper: misses must not consult icon preferences."""
from ios_icons_stubs import fixtures
from test_render_work_reuse import JAVA, probe


def test_unmapped_resources_do_not_repeat_configuration_lookups(tmp_path):
    files = fixtures()
    files['android/content/res/Resources.java'] = '''package android.content.res;import android.graphics.drawable.*;
public class Resources{
 public static class Theme{}public int density=320,decodes;private java.util.Map<Integer,Object>pixels=new java.util.HashMap<>();
 public Resources(){}public Resources(Object a,Object m,Object c){}public Object getAssets(){return this;}public Object getDisplayMetrics(){return this;}public Object getConfiguration(){return this;}
 public Drawable getDrawable(int id){return getDrawableForDensity(id,0,null);}public Drawable getDrawable(int id,Theme t){return getDrawableForDensity(id,0,t);}public Drawable getDrawableForDensity(int id,int d){return getDrawableForDensity(id,d,null);}
 public Drawable getDrawableForDensity(int id,int dpi,Theme theme){Object data=pixels.get(id);if(data==null){data=new Object();pixels.put(id,data);decodes++;}return new Fake(data,dpi==0?density:dpi,32,32);}
}'''
    files['Probe.java'] = '''import app.flexygram.icons.*;import android.content.res.Resources;import android.graphics.drawable.*;import app.exteraless.icons.BaseIconPacks;import org.telegram.messenger.R;
public class Probe{static void check(boolean ok){if(!ok)throw new AssertionError();}public static void main(String[]args){
 CupertinoResources resources=new CupertinoResources(new Resources());
 for(int pack:new int[]{0,1,2,3}){BaseIconPacks.selected=pack;int before=BaseIconPacks.reads;
 for(int i=0;i<1000;i++)check(resources.getDrawable(123456789)!=null);
 check(BaseIconPacks.reads==before);}
 for(int pack:new int[]{0,3}){BaseIconPacks.selected=pack;int before=BaseIconPacks.reads;Drawable icon=resources.getDrawable(R.drawable.input_attach);
 check(icon!=null&&!(icon instanceof Fake)&&BaseIconPacks.reads==before+1);}
 for(int pack:new int[]{1,2}){BaseIconPacks.selected=pack;check(resources.getDrawable(R.drawable.input_attach) instanceof Fake);}
}}
'''
    actual = [JAVA/'app/flexygram/icons'/name for name in ['CupertinoResources.java','ExactIcons.java','ExactIconMap.java','OriginalIconDrawable.java']]
    probe(tmp_path, files, actual)
