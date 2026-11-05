"""Execute the real filter-tab callback: visual fades must not drive list layout."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_search_frames_skip_list_layout_but_geometry_changes_still_request_it(tmp_path):
    source = (JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    methods = '\n'.join(method(source, s) for s in [
        'private float getFilterTabsVisibilityFactor(boolean includeSearch)',
        'private void checkUi_filterTabsVisible()'])
    assert 'filterTabsView = null;\n        lastFilterTabsLayoutFactor = Float.NaN;' in source
    probe(tmp_path, {'Probe.java': '''public class Probe {
        static class View {
            static final int VISIBLE=0,GONE=8;float alpha=1,sx=1,sy=1;int visibility,layouts;
            void setAlpha(float f){alpha=f;}void setScaleX(float f){sx=f;}void setScaleY(float f){sy=f;}
            void setVisibility(int v){visibility=v;}void requestLayout(){layouts++;}
        }
        static class Factor {float value;float getFloatValue(){return value;}}
        static class Page {View listView=new View();}
        View filterTabsView=new View();Page[] viewPages={new Page()};
        Factor animatorSearchVisible=new Factor(),animatorFilterTabsVisible=new Factor();
        float sliding,lastFilterTabsLayoutFactor=Float.NaN;int contextUpdates;
        float getRightSlidingProgress(){return sliding;}
        void updateContextViewPosition(){contextUpdates++;}
        static float lerp(float a,float b,float f){return a+(b-a)*f;}
        METHODS
        static void check(boolean b){if(!b)throw new AssertionError();}
        public static void main(String[] args){
            Probe p=new Probe();p.animatorFilterTabsVisible.value=1;p.checkUi_filterTabsVisible();
            check(p.viewPages[0].listView.layouts==1);
            for(int i=0;i<=120;i++){p.animatorSearchVisible.value=i/120f;p.checkUi_filterTabsVisible();}
            check(p.viewPages[0].listView.layouts==1&&p.filterTabsView.visibility==View.GONE);
            for(int i=120;i>=0;i--){p.animatorSearchVisible.value=i/120f;p.checkUi_filterTabsVisible();}
            check(p.filterTabsView.alpha==1&&p.filterTabsView.sx==1&&p.viewPages[0].listView.layouts==1);
            p.animatorSearchVisible.value=1;p.checkUi_filterTabsVisible();
            // Even fully transparent tabs must update list geometry if their reservation changes.
            p.animatorFilterTabsVisible.value=.5f;p.checkUi_filterTabsVisible();
            check(p.viewPages[0].listView.layouts==2);
            p.sliding=.5f;p.checkUi_filterTabsVisible();check(p.viewPages[0].listView.layouts==3);
            p.checkUi_filterTabsVisible();check(p.viewPages[0].listView.layouts==3);
            Page page=p.viewPages[0];p.viewPages[0]=null;p.sliding=1;p.checkUi_filterTabsVisible();
            p.viewPages[0]=page;p.checkUi_filterTabsVisible();check(page.listView.layouts==4);
            p.lastFilterTabsLayoutFactor=Float.NaN;p.checkUi_filterTabsVisible();check(page.listView.layouts==5);
            p.filterTabsView=null;int before=p.contextUpdates;p.checkUi_filterTabsVisible();check(p.contextUpdates==before+1);
        }
    }'''.replace('METHODS', methods)})
