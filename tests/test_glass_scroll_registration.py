"""Exercise production scroll registration across duplicate calls and reattachment."""
import re
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_scroll_listeners_register_once_and_survive_reattachment(tmp_path):
    source = (JAVA/'org/telegram/utils/glass/GlassEngine.java').read_text()
    field = re.search(r'private final WeakHashMap<[^;]+registeredScrolledViews\s*=\s*[^;]+;', source).group(0)
    methods = '\n'.join(method(source, anchor) for anchor in [
        'public void addScrolledView(ViewPager', 'public void addScrolledView(RecyclerListView'])
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 @interface NonNull{}
 static class View{
  interface OnAttachStateChangeListener{void onViewAttachedToWindow(View v);void onViewDetachedFromWindow(View v);}
  final List<OnAttachStateChangeListener> attachments=new ArrayList<>();
  void addOnAttachStateChangeListener(OnAttachStateChangeListener l){attachments.add(l);}
  void removeOnAttachStateChangeListener(OnAttachStateChangeListener l){attachments.remove(l);}
  void detach(){for(var l:new ArrayList<>(attachments))l.onViewDetachedFromWindow(this);}
  void attach(){for(var l:new ArrayList<>(attachments))l.onViewAttachedToWindow(this);}
 }
 static class ViewPager extends View{
  static class SimpleOnPageChangeListener{public void onPageScrolled(int p,float offset,int px){}}
  final List<SimpleOnPageChangeListener> listeners=new ArrayList<>();
  void addOnPageChangeListener(SimpleOnPageChangeListener l){listeners.add(l);}
  void removeOnPageChangeListener(SimpleOnPageChangeListener l){listeners.remove(l);}
  void scroll(){for(var l:listeners)l.onPageScrolled(1,.5f,10);}
 }
 static class RecyclerView extends View{
  static class OnScrollListener{public void onScrollStateChanged(RecyclerView v,int state){}public void onScrolled(RecyclerView v,int dx,int dy){}}
 }
 static class RecyclerListView extends RecyclerView{
  interface Edge{void changed(int direction,boolean visible);}
  final List<OnScrollListener> listeners=new ArrayList<>();final List<Edge> edges=new ArrayList<>();
  void addOnScrollListener(OnScrollListener l){listeners.add(l);}void removeOnScrollListener(OnScrollListener l){listeners.remove(l);}
  void addEdgeEffectListener(Edge l){edges.add(l);}
  void scroll(){for(var l:listeners){l.onScrollStateChanged(this,1);l.onScrolled(this,0,10);}for(var l:edges)l.changed(1,true);}
 }
 FIELD
 long scrollGenerationId,scrollEdgesGenerationId;
 METHODS
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();ViewPager pager=new ViewPager();RecyclerListView list=new RecyclerListView();
  p.addScrolledView((ViewPager)null);p.addScrolledView((RecyclerListView)null);
  for(int i=0;i<100;i++){p.addScrolledView(pager);p.addScrolledView(list);}
  check(pager.listeners.size()==1&&list.listeners.size()==1&&list.edges.size()==1);
  pager.scroll();list.scroll();check(p.scrollGenerationId==3&&p.scrollEdgesGenerationId==1);
  for(int i=0;i<20;i++){
   pager.detach();list.detach();pager.attach();list.attach();
   pager.scroll();list.scroll();check(p.scrollGenerationId==3L*(i+2)&&p.scrollEdgesGenerationId==i+2);
   p.addScrolledView(pager);p.addScrolledView(list);
   check(pager.listeners.size()==1&&list.listeners.size()==1&&list.edges.size()==1);
  }
  for(Object value:p.registeredScrolledViews.values())check(value instanceof Boolean);
 }
}'''.replace('FIELD',field).replace('METHODS',methods)})
