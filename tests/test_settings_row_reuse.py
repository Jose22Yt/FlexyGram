"""Run the real row background/icon methods with counted Android drawable doubles."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_settings_row_reuses_drawables_and_updates_theme_geometry_resources(tmp_path):
    source = (JAVA/'app/flexygram/settings/signature/Settings2Cell.java').read_text()
    fields = source[source.index('    private int cardColor'):source.index('    public void setCardEdges')]
    methods = '\n'.join(method(source, signature) for signature in [
        'private void updateCard()', 'private void bindIcon(int resource)'])
    files = {
        'android/content/res/ColorStateList.java': 'package android.content.res; public class ColorStateList {public int color; public static ColorStateList valueOf(int c){ColorStateList s=new ColorStateList();s.color=c;return s;}}',
        'android/content/res/Configuration.java': '''package android.content.res; public class Configuration {
            public int version; public Configuration(){} public Configuration(Configuration c){version=c.version;}
            public boolean equals(Object o){return o instanceof Configuration && version==((Configuration)o).version;}}''',
        'android/content/res/Resources.java': '''package android.content.res; public class Resources {
            public Configuration config=new Configuration(); public Configuration getConfiguration(){return config;}}''',
        'android/graphics/drawable/GradientDrawable.java': '''package android.graphics.drawable; public class GradientDrawable {
            public static int instances;public int color,colors,radii;public float[] corners;
            public GradientDrawable(){instances++;}public void setColor(int c){color=c;colors++;}
            public void setCornerRadii(float[] r){corners=r.clone();radii++;}}''',
        'android/graphics/drawable/RippleDrawable.java': '''package android.graphics.drawable; public class RippleDrawable {
            public static int instances; public int color;public RippleDrawable(android.content.res.ColorStateList c,Object f,Object m){instances++;color=c.color;}
            public void setColor(android.content.res.ColorStateList c){color=c.color;}}''',
        'android/graphics/drawable/InsetDrawable.java': '''package android.graphics.drawable; public class InsetDrawable {
            public static int instances; public int gap; public InsetDrawable(Object d,int a,int b,int c,int g){instances++;gap=g;}}''',
        'Probe.java': '''public class Probe {
            static class Theme {static int key_windowBackgroundGray=0,key_windowBackgroundWhite=1,key_listSelector=2,key_windowBackgroundWhiteBlueHeader=3;static boolean isCurrentThemeDark(){return true;}
                static int[] colors={1,2,3,4};static int getColor(int k,Object p){return colors[k];}}
            static class SettingsCardStyle {static int OUTER_RADIUS=20,INNER_RADIUS=6,GAP=4;static int surface(int a,int b,int c,boolean dark){return a+b;}}
            static class SettingsCategoryIcon {static int creates;static Object create(Object c,int r,Object provider){creates++;return r<=0?null:new Object();}}
            static class Icon {Object drawable;void setImageDrawable(Object d){drawable=d;}}
            final Icon icon=new Icon();static class Provider {boolean isDark(){return true;}}Provider provider;Object background;int sets;boolean first,last;float density=1;
            android.content.res.Resources resources=new android.content.res.Resources();
            android.content.res.Resources getResources(){return resources;}Object getContext(){return this;}
            int dp(float v){return Math.round(v*density);}Object getBackground(){return background;}
            void setBackground(Object b){background=b;sets++;}
            FIELDS
            METHODS
            static void check(boolean b){if(!b)throw new AssertionError();}
            public static void main(String[] args){
                Probe p=new Probe();p.updateCard();Object bg=p.background;p.bindIcon(42);Object icon=p.icon.drawable;
                for(int i=0;i<10000;i++){p.updateCard();p.bindIcon(42);}
                check(p.background==bg&&p.sets==1&&p.icon.drawable==icon&&SettingsCategoryIcon.creates==1);
                check(android.graphics.drawable.GradientDrawable.instances==2&&p.cardFill.radii==1&&p.cardFill.colors==1);
                check(android.graphics.drawable.RippleDrawable.instances==1&&android.graphics.drawable.InsetDrawable.instances==1);
                p.first=true;p.updateCard();check(p.cardFill.corners[0]==20&&p.cardFill.corners[7]==6);
                p.last=true;p.updateCard();check(p.cardMask.corners[7]==20&&p.background==bg);
                Theme.colors[1]=100;Theme.colors[2]=200;p.updateCard();
                check(p.cardFill.color==101&&p.cardRipple.color==200&&p.background==bg);
                p.density=2;p.updateCard();check(p.cardFill.corners[0]==40&&p.cardBackground.gap==8);
                p.background=null;p.updateCard();check(p.background==p.cardBackground);
                p.bindIcon(43);check(p.icon.drawable!=icon);p.bindIcon(0);check(p.icon.drawable==null);
                p.bindIcon(42);icon=p.icon.drawable;p.resources.config.version++;p.bindIcon(42);check(p.icon.drawable!=icon);
                icon=p.icon.drawable;p.resources=new android.content.res.Resources();p.bindIcon(42);check(p.icon.drawable!=icon);
                Probe other=new Probe();other.updateCard();other.bindIcon(42);
                check(other.background!=p.background&&other.icon.drawable!=p.icon.drawable);
            }
        }'''.replace('FIELDS', fields).replace('METHODS', methods),
    }
    probe(tmp_path, files)


def test_visible_settings_text_follows_theme_without_redundant_updates(tmp_path):
    source = (JAVA/'app/flexygram/settings/signature/Settings2Cell.java').read_text()
    update = method(source, 'private void updateForeground()')
    probe(tmp_path, {'Probe.java': '''public class Probe {
        static class Theme {
            static int key_windowBackgroundWhiteBlackText=0,key_windowBackgroundWhiteGrayText2=1;
            static int[] colors={0xff111111,0xff777777};
            static int getColor(int k,Object p){return colors[k];}
        }
        static class Text {int color,sets;void setTextColor(int c){color=c;sets++;}}
        static class Icon {int color,sets;void setColorFilter(int c){color=c;sets++;}}
        Text title=new Text(),description=new Text();Icon icon=new Icon();Object provider;
        int lastIconColor,lastDescriptionColor;boolean foregroundInitialized;
        UPDATE
        static void check(boolean b){if(!b)throw new AssertionError();}
        public static void main(String[] args){
            Probe p=new Probe();p.updateForeground();
            for(int i=0;i<10000;i++)p.updateForeground();
            check(p.title.sets==1&&p.description.sets==1&&p.icon.sets==1);
            Theme.colors[0]=0xffeeeeee;Theme.colors[1]=0xffaaaaaa;p.updateForeground();
            check(p.title.color==Theme.colors[0]&&p.icon.color==Theme.colors[0]&&p.description.color==Theme.colors[1]);
            check(p.title.sets==2&&p.description.sets==2&&p.icon.sets==2);
            Theme.colors[1]=0xff999999;p.updateForeground();check(p.title.sets==2&&p.description.sets==3);
            p.foregroundInitialized=false;p.updateForeground();check(p.icon.sets==3);
        }
    }'''.replace('UPDATE', update)})
