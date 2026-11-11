#!/usr/bin/env python3
"""Compare actual baseline/current metadata loaders in fresh host JVMs; no APK or FPS claim."""
import argparse,json,pathlib,re,statistics,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
BASE='c68627aba75861f4a9d3fac611f810406845344d'
MAP='TMessagesProj/src/main/java/app/flexygram/icons/ExactIconMap.java'


def measure(source,baseline,samples):
    names=sorted(set(re.findall(r'R\.drawable\.(\w+)',source)))
    fields=''.join(f'public static int {n}={len(names)+100-i};'for i,n in enumerate(names))
    if baseline:
        lookup='var e=ExactIconMap.get(id);return e==null?0:e.asset^e.color;'
    else:
        lookup='long e=ExactIconMap.find(id);return e==0?0:ExactIconMap.asset(e)^ExactIconMap.color(e);'
    probe='''package app.flexygram.icons;
import java.lang.management.ManagementFactory;
public class LookupMeasure {
 static volatile long sink;
 static int lookup(int id){LOOKUP}
 public static void main(String[]args){
  int firstId=org.telegram.messenger.R.drawable.input_smile; // Resolve the synthetic R class outside the metadata measurement.
  var bean=(com.sun.management.ThreadMXBean)ManagementFactory.getThreadMXBean();
  if(!bean.isThreadAllocatedMemorySupported())throw new AssertionError("thread allocation counters required");
  bean.setThreadAllocatedMemoryEnabled(true);long thread=Thread.currentThread().threadId();
  bean.getThreadAllocatedBytes(thread);bean.getThreadAllocatedBytes(thread);
  long bytes=bean.getThreadAllocatedBytes(thread),start=System.nanoTime();
  sink=lookup(firstId);
  long elapsed=System.nanoTime()-start,initial=bean.getThreadAllocatedBytes(thread)-bytes;
  int[]ids={IDS};long checksum=0;
  for(int i=0;i<200000;i++)checksum+=lookup(ids[i%ids.length]);sink=checksum;
  bytes=bean.getThreadAllocatedBytes(thread);start=System.nanoTime();
  for(int i=0;i<1000000;i++)checksum+=lookup(ids[i%ids.length]);
  long steady=System.nanoTime()-start,alloc=bean.getThreadAllocatedBytes(thread)-bytes;sink=checksum;
  System.out.println("{\\"init_alloc_bytes\\":"+initial+",\\"init_nanos\\":"+elapsed+",\\"million_lookup_alloc_bytes\\":"+alloc+",\\"million_lookup_nanos\\":"+steady+"}");
 }
}'''.replace('LOOKUP',lookup).replace('IDS',','.join('org.telegram.messenger.R.drawable.'+n for n in names[::max(1,len(names)//32)]))
    with tempfile.TemporaryDirectory(prefix='flexy-icon-lookup-')as tmp:
        tmp=pathlib.Path(tmp);files={
            'app/flexygram/icons/ExactIconMap.java':source,
            'app/flexygram/icons/LookupMeasure.java':probe,
            'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R{public static class drawable{'+fields+'}}'}
        for name,text in files.items():p=tmp/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(tmp),*map(str,tmp.rglob('*.java'))],check=True,capture_output=True,text=True)
        results=[json.loads(subprocess.check_output(['java','-cp',str(tmp),'app.flexygram.icons.LookupMeasure'],text=True))for _ in range(samples)]
    return {'samples':results,'median':{key:statistics.median(r[key]for r in results)for key in results[0]}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=pathlib.Path);parser.add_argument('--samples',type=int,default=7);args=parser.parse_args()
    old=subprocess.check_output(['git','show',BASE+':'+MAP],cwd=ROOT,text=True)
    result={'baseline_commit':BASE,'scope':'Isolated host JVM metadata lookup with non-final synthetic R IDs, not Android startup, frame timing or device memory.',
            'java':subprocess.run(['java','-version'],capture_output=True,text=True).stderr.splitlines()[0],
            'baseline':measure(old,True,args.samples),'current':measure((ROOT/MAP).read_text(),False,args.samples)}
    text=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.write_text(text)
    print(json.dumps({key:result[key]['median']for key in ['baseline','current']},indent=2))

if __name__=='__main__':main()
