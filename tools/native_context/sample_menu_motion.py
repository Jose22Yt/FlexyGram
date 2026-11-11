#!/usr/bin/env python3
"""Sample actual old/current message-menu controllers with a deterministic host frame clock.
No app rendering, device FPS or reproduction of the uploaded screen recording is claimed.
"""
import argparse,json,pathlib,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE='912ef3b1386012dd491bad771db55154629aedac'
JAVA='TMessagesProj/src/main/java/'


def sample(baseline):
    # Keep the tool independent from pytest/test imports: only the two small Android clock doubles.
    import ast
    tree=ast.parse((ROOT/'tests/motion43_support.py').read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='frames')
    files=ast.literal_eval(function.body[0].value)
    names=['app/exteraless/player/Spring.java','app/flexygram/bubbles/interaction/SelectedBubbleMotion.java']
    for name in names:
        files[name]=subprocess.check_output(['git','show',BASE+':'+JAVA+name],cwd=ROOT,text=True)if baseline else (ROOT/JAVA/name).read_text()
    files['MotionSample.java']='''import app.flexygram.bubbles.interaction.SelectedBubbleMotion;import android.view.Choreographer;
public class MotionSample{
 public static void main(String[]args){StringBuilder out=new StringBuilder("[");boolean comma=false;
 for(int hz:new int[]{30,60,90,120,144}){
  android.os.SystemClock.now=1000;long base=1000000000L;var m=new SelectedBubbleMotion();m.enter(()->{});float peak=m.panelScale();int frame=0;
  if(comma)out.append(',');comma=true;out.append("{\\"hz\\":").append(hz).append(",\\"points\\":[");
  out.append("[0,").append(m.panelScale()).append(',').append(m.scaleX()).append(',').append(m.backdropProgress()).append(']');
  while(m.isRunning()&&frame<hz){frame++;long time=base+Math.round(frame*1000000000d/hz);Choreographer.getInstance().frame(time);
   if(frame==Math.max(1,Math.round(hz*.08f)))m.backdropReady();
   peak=Math.max(peak,m.panelScale());out.append(",[").append(frame*1000d/hz).append(',').append(m.panelScale()).append(',').append(m.scaleX()).append(',').append(m.backdropProgress()).append(']');
  }
  out.append("],\\"settled_ms\\":").append(frame*1000d/hz).append(",\\"peak_scale\\":").append(peak);
  int start=frame;int[]done={0};m.close(()->done[0]++);
  while(m.hasOwner()&&frame-start<hz){frame++;Choreographer.getInstance().frame(base+Math.round(frame*1000000000d/hz));}
  if(done[0]!=1||Choreographer.getInstance().pending!=null)throw new AssertionError("cleanup");
  out.append(",\\"close_ms\\":").append((frame-start)*1000d/hz).append('}');m.reset();
 }out.append(']');System.out.println(out);}
}'''
    with tempfile.TemporaryDirectory(prefix='bubble-motion-sample-')as tmp:
        tmp=pathlib.Path(tmp)
        for name,text in files.items():p=tmp/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(tmp),*map(str,tmp.rglob('*.java'))],check=True,capture_output=True,text=True)
        return json.loads(subprocess.check_output(['java','-cp',str(tmp),'MotionSample'],text=True))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);args=p.parse_args()
    result={'baseline_commit':BASE,'scope':'Production controllers sampled in a host JVM with deterministic frame callbacks; not app/device frame rates. Points: elapsed_ms, menu_scale, message_scale_x, backdrop_progress. Capture ready after approximately 80ms.',
            'baseline':sample(True),'current':sample(False)}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    for key in ['baseline','current']:print(key,[{k:v for k,v in item.items()if k!='points'}for item in result[key]])

if __name__=='__main__':main()
