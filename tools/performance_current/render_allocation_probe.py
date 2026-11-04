#!/usr/bin/env python3
"""Compare exact baseline/current section geometry and JVM allocation bytes. Never builds an APK."""
import hashlib,json,re,subprocess,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from test_composer_layout import method
BASE='b0fbc63a810f07d8d99427982805926fa0f93d2c'
FILE='TMessagesProj/src/main/java/org/telegram/ui/Components/RecyclerListView.java'
old=subprocess.check_output(['git','show',BASE+':'+FILE],cwd=ROOT,text=True)
current=(ROOT/FILE).read_text()
old_drawer=re.sub(r'\bSectionsDrawer\b','BaselineDrawer',method(old,'public static class SectionsDrawer'))
drawer=method(current,'public static class SectionsDrawer')
obtain=method(current,'private SectionsDrawer.Section obtainAnimatedSection(')
source='''import java.util.*;import java.lang.management.ManagementFactory;
public class RenderAllocationProbe {
 static int dp(float n){return Math.round(n);}static float lerp(float a,float b,float t){return a+(b-a)*t;}
 static class Utilities{interface Callback5<A,B,C,D,E>{void run(A a,B b,C c,D d,E e);}}
 OLD
 CURRENT
 private ArrayList<SectionsDrawer.Section> sectionPool;
 OBTAIN
 static volatile double sink;
 static final Utilities.Callback5<Float,Float,Float,Float,Float> OUTPUT=(a,b,t,d,x)->sink=a+b+t+d+x;
 final List<SectionsDrawer.Section> rows=new ArrayList<>();final List<BaselineDrawer.Section> before=new ArrayList<>();
 void frame(boolean baseline,int count,boolean segmented){
  if(baseline){before.clear();for(int i=0;i<count;i++)before.add(new BaselineDrawer.Section(i*100,i*100+40,1,false));BaselineDrawer.draw(before,28,OUTPUT,segmented,6,4);}
  else{rows.clear();for(int i=0;i<count;i++)rows.add(obtainAnimatedSection(i,i*100,i*100+40,1,false));SectionsDrawer.draw(rows,28,OUTPUT,segmented,6,4);}
 }
 static void geometry(){
  Random random=new Random(94131);
  for(int trial=0;trial<1000;trial++)for(boolean segmented:new boolean[]{false,true}){
   List<BaselineDrawer.Section> old=new ArrayList<>();List<SectionsDrawer.Section> now=new ArrayList<>();
   for(int i=0,n=random.nextInt(40);i<n;i++){
    float from=random.nextInt(500)-100,to=from+random.nextInt(80);float alpha=new float[]{0,.0005f,.2f,.7f,1}[random.nextInt(5)];boolean round=random.nextBoolean();
    old.add(new BaselineDrawer.Section(from,to,alpha,round));now.add(new SectionsDrawer.Section(from,to,alpha,round));
   }
   List<float[]> a=new ArrayList<>(),b=new ArrayList<>();
   BaselineDrawer.draw(old,28,(f,t,top,bottom,x)->a.add(new float[]{f,t,top,bottom,x}),segmented,6,4);
   SectionsDrawer.draw(now,28,(f,t,top,bottom,x)->b.add(new float[]{f,t,top,bottom,x}),segmented,6,4);
   if(a.size()!=b.size())throw new AssertionError("shape count changed");
   for(int i=0;i<a.size();i++)if(!Arrays.equals(a.get(i),b.get(i)))throw new AssertionError("shape or alpha changed");
  }
 }
 public static void main(String[]args){
  geometry();
  com.sun.management.ThreadMXBean bean=(com.sun.management.ThreadMXBean)ManagementFactory.getThreadMXBean();
  if(!bean.isThreadAllocatedMemorySupported())throw new IllegalStateException("JVM allocation counters unavailable");
  bean.setThreadAllocatedMemoryEnabled(true);long thread=Thread.currentThread().getId();
  System.out.print("{\\\"geometry_comparisons\\\":2000,\\\"samples\\\":[");boolean first=true;
  for(int count:new int[]{16,64})for(boolean segmented:new boolean[]{false,true}){
   RenderAllocationProbe probe=new RenderAllocationProbe();
   for(int i=0;i<10000;i++){probe.frame(true,count,segmented);probe.frame(false,count,segmented);}
   long start=bean.getThreadAllocatedBytes(thread);for(int i=0;i<10000;i++)probe.frame(true,count,segmented);long oldBytes=bean.getThreadAllocatedBytes(thread)-start;
   start=bean.getThreadAllocatedBytes(thread);for(int i=0;i<10000;i++)probe.frame(false,count,segmented);long newBytes=bean.getThreadAllocatedBytes(thread)-start;
   if(!first)System.out.print(",");first=false;
   System.out.printf(java.util.Locale.ROOT,"{\\\"rows\\\":%d,\\\"segmented\\\":%s,\\\"baseline_bytes_per_frame\\\":%.1f,\\\"candidate_bytes_per_frame\\\":%.1f}",count,segmented,oldBytes/10000.,newBytes/10000.);
  }
  System.out.println("]}");
 }
}'''.replace(' OLD\n',old_drawer+'\n').replace(' CURRENT\n',drawer+'\n').replace(' OBTAIN\n',obtain+'\n')
# Java literals above need one escaping layer, not shell interpolation.
source=source.replace('\\\\"','\\"')
with tempfile.TemporaryDirectory(prefix='flexy-render-allocation-') as tmp:
 path=Path(tmp)/'RenderAllocationProbe.java';path.write_text(source)
 subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(path)],check=True,capture_output=True)
 result=subprocess.run(['java','-Xbatch','-cp',tmp,'RenderAllocationProbe'],capture_output=True,text=True,check=True)
 data=json.loads(result.stdout);data.update({'baseline':BASE,'source_sha256':hashlib.sha256(current.encode()).hexdigest(),'java':subprocess.check_output(['java','--version'],text=True).splitlines()[0],'warmup_iterations':10000,'measured_iterations':10000,'flags':['-Xbatch'],'scope':'HotSpot JVM geometry/allocated bytes; Android Views, HWUI, FPS, PSS and thermal behavior NOT_MEASURED'})
 print(json.dumps(data,indent=2))
