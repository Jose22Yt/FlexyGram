"""Host checks for settings-only sizing, semantic resources and live theme tint."""
import pathlib
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import pytest


@pytest.mark.skipif(not shutil.which("javac") or not shutil.which("java"), reason="JDK required")
def test_settings_icons_size_theme_and_recycling():
    root = pathlib.Path(__file__).resolve().parents[1] / "TMessagesProj/src/main"
    resources = sorted((root / "res/drawable").glob("fg_settings_*.xml"))
    android = "{http://schemas.android.com/apk/res/android}"
    assert resources
    for resource in resources:
        vector = ET.parse(resource).getroot()
        assert vector.attrib[android + "width"] == "24dp"
        assert vector.attrib[android + "height"] == "24dp"
        assert vector.find("path").attrib[android + "strokeWidth"] == "1.8"

    stubs = {
        "android.util.SparseIntArray": "public class SparseIntArray {private java.util.Map<Integer,Integer> data=new java.util.HashMap<>();public int get(int k,int d){return data.getOrDefault(k,d);}public void put(int k,int v){data.put(k,v);}public void clear(){data.clear();}public int size(){return data.size();}}",
        "android.graphics.Canvas": "public class Canvas {}",
        "android.graphics.PorterDuff": "public class PorterDuff {public enum Mode {SRC_IN}}",
        "android.graphics.PorterDuffColorFilter": "public class PorterDuffColorFilter {public int color;public PorterDuffColorFilter(int c,PorterDuff.Mode mode){color=c;}}",
        "android.content.res.Resources": """public class Resources {
            public static class NotFoundException extends RuntimeException {}
            public String getResourceEntryName(int id){if(id==1000)return "msg_discussion";if(id==1001)return "cloud_sync";if(id==1002)return "custom_plugin_icon";throw new NotFoundException();}
        }""",
        "android.content.Context": """public class Context {
            public android.content.res.Resources getResources(){return new android.content.res.Resources();}
        }""",
        "org.telegram.ui.ActionBar.Theme": """public class Theme {
            public interface ResourcesProvider {}
            public static final int key_windowBackgroundWhiteBlackText=1;
            public static int foreground=0xff17191c;
            public static int getColor(int key,ResourcesProvider provider){return foreground;}
        }""",
        "org.telegram.ui.Cells.TextCell": """public class TextCell {
            public static class Icon {
                public Object background=new Object(),filter;public int padding=7;public float translation=2;public int resource;
                public void setImageResource(int id){resource=id;}public void setBackground(Object b){background=b;}
                public void setPadding(int a,int b,int c,int d){padding=a+b+c+d;}
                public void setTranslationX(float value){translation=value;}
                public Object getColorFilter(){return filter;}public void setColorFilter(Object f){filter=f;}
            }
            public final Icon imageView=new Icon();public boolean isIcon;public int imageLeft,offset,width;
            public CharSequence title,value;private android.content.Context context;
            public TextCell(android.content.Context c,org.telegram.ui.ActionBar.Theme.ResourcesProvider r){context=c;}
            public android.content.Context getContext(){return context;}
            public void setIsIcon(boolean value){isIcon=value;}
            public void setImageLeft(int value){imageLeft=value;}public void setOffsetFromImage(int value){offset=value;}
            public void setTextAndIcon(CharSequence text,int icon,boolean divider){title=text;imageView.resource=icon;isIcon=false;}
            public void setTextAndValueAndIcon(CharSequence text,CharSequence v,boolean animated,int icon,boolean divider){setTextAndIcon(text,icon,divider);value=v;}
            public void setTextAndSpoilersValueAndIcon(String text,CharSequence v,int icon,boolean divider){setTextAndIcon(text,icon,divider);value=v;}
            public void setTextAndCheckAndIcon(CharSequence text,boolean checked,int icon,boolean divider){setTextAndIcon(text,icon,divider);}
            public void setColorfulIcon(int a,int b,int icon){}
            protected void onMeasure(int w,int h){width=isIcon?24:96;}
            protected void dispatchDraw(android.graphics.Canvas c){}
        }""",
    }
    values = ";".join(f"public static int {path.stem}={i+1}" for i, path in enumerate(resources)) + ";"
    stubs["org.telegram.messenger.R"] = "public class R {public static class drawable {" + values + "}}"
    harness = """
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.PorterDuffColorFilter;
import app.exteraless.settings.utils.*;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.messenger.R;
public class SettingsIconsRegression extends CompactSettingsTextCell {
    SettingsIconsRegression(){super(new Context(),null);}
    static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args){
        SettingsIconsRegression cell=new SettingsIconsRegression();
        cell.setTextAndIcon("Conversaciones",1000,true);cell.onMeasure(360,64);cell.dispatchDraw(new Canvas());
        require(cell.imageView.resource==R.drawable.fg_settings_chat,"replace known category with outline icon");
        require(cell.width==24&&cell.imageLeft==20&&cell.offset==60,"normalize large icons after binding");
        require(cell.imageView.background==null&&cell.imageView.padding==0,"remove colored icon tile without changing row");
        Object first=cell.imageView.getColorFilter();
        require(((PorterDuffColorFilter)first).color==0xff17191c,"dark icon in light theme");
        Theme.foreground=0xfff1f3f5;cell.dispatchDraw(new Canvas());
        require(((PorterDuffColorFilter)cell.imageView.getColorFilter()).color==0xfff1f3f5,"light icon after live night-mode transition");
        Object night=cell.imageView.getColorFilter();cell.dispatchDraw(new Canvas());
        require(night==cell.imageView.getColorFilter(),"do not allocate tint every frame");
        cell.setTextAndValueAndIcon("Copias","Configurado",false,1001,true);cell.imageView.setColorFilter(first);
        cell.onMeasure(360,64);cell.dispatchDraw(new Canvas());
        require(cell.width==24&&cell.imageView.getColorFilter()==night,"recycling restores icon size and active tint");
        require("Configurado".contentEquals(cell.value),"preserve setting values");
        cell.setTextAndIcon("Plugin",1002,false);require(cell.imageView.resource==1002,"preserve unfamiliar plugin icon semantics");
        require(SettingsIcons.resolve(new Context(),0)==0,"retain absent icons");
        require(SettingsIcons.resolve(new Context(),-1)==-1,"safe resource lookup fallback");
        require(!SettingsIcons.appliesTo(new Object()),"style does not affect other app lists");
    }
}
"""
    with tempfile.TemporaryDirectory(prefix="flexygram-settings-icons-") as directory:
        temp = pathlib.Path(directory)
        sources = []
        for name, body in stubs.items():
            package = name.rsplit(".", 1)[0]
            path = temp / (name.replace(".", "/") + ".java")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"package {package};\n{body}")
            sources.append(str(path))
        main = temp / "SettingsIconsRegression.java"
        main.write_text(harness)
        sources += [str(main), str(root / "java/app/exteraless/settings/utils/SettingsIcons.java"), str(root / "java/app/exteraless/settings/utils/CompactSettingsTextCell.java")]
        result = subprocess.run(["javac", "-d", directory, *sources], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        result = subprocess.run(["java", "-cp", directory, "SettingsIconsRegression"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
