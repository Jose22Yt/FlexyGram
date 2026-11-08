#!/usr/bin/env python3
"""Real lyrics RecyclerView, parser and clock with explicit playback/provider doubles, no APK."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('music_pipeline',HERE.parent/'music_visual/run.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
spec=importlib.util.spec_from_file_location('music_stubs',HERE.parent/'music_visual/stubs.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def write_stubs(source,root):
 base.write_stubs(source,root)
 def put(path,text):
  p=source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 player=root/'TMessagesProj/src/main/java/app/exteraless/player'
 for name in ('LyricsView','Lyrics','LyricsFill'):
  put('app/exteraless/player/'+name+'.java',(player/(name+'.java')).read_text())
 import re
 r=source/'org/telegram/messenger/R.java';text=r.read_text();names=sorted(set(re.findall(r'R.string.(\w+)',(player/'LyricsView.java').read_text()))-set(re.findall(r'int (\w+)=',text)))
 text=text.replace('public static class string {','public static class string {'+''.join('public static final int '+n+'='+str(1000+i)+';' for i,n in enumerate(names)));r.write_text(text)
 put('tw/nekomimi/nekogram/helpers/TypefaceHelper.java','package tw.nekomimi.nekogram.helpers;public class TypefaceHelper{public static android.graphics.Typeface lyricsTypeface(){return android.graphics.Typeface.create("sans-serif",1);}}')
 put('org/telegram/ui/Components/RadialProgressView.java','package org.telegram.ui.Components;public class RadialProgressView extends android.view.View{public RadialProgressView(android.content.Context c){super(c);}public void setSize(int v){}public void setProgressColor(int c){}}')
 put('org/telegram/ui/Components/RecyclerListView.java','''package org.telegram.ui.Components;import android.content.*;import android.view.*;import androidx.recyclerview.widget.RecyclerView;public class RecyclerListView extends RecyclerView{
 public java.util.ArrayList<RecyclerView.OnScrollListener> listeners=new java.util.ArrayList<>();public void addOnScrollListener(RecyclerView.OnScrollListener listener){super.addOnScrollListener(listener);listeners.add(listener);}public void simulateScrollState(int state){for(var l:listeners)l.onScrollStateChanged(this,state);}
 public RecyclerListView(Context c){super(c);}public void setSelectorDrawableColor(int color){}
 public interface OnItemClickListener{void onItemClick(View v,int position);}public OnItemClickListener click;public void setOnItemClickListener(OnItemClickListener l){click=l;}
 public static class Holder extends RecyclerView.ViewHolder{public Holder(View v){super(v);}}
 public abstract static class SelectionAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder>{public abstract boolean isEnabled(RecyclerView.ViewHolder h);}}
 ''')
 # Music layout fixtures are not needed in the lyrics suite.
 (source/'app/exteraless/player/LayoutFixture.java').unlink()
if __name__=='__main__':raise SystemExit(pipeline.main(here=HERE,test_class='LyricsUiTest',stubs_writer=write_stubs,extra_aars=[('androidx.recyclerview','recyclerview','1.4.0'),('androidx.customview','customview','1.2.0'),('androidx.customview','customview-poolingcontainer','1.0.0')]))
