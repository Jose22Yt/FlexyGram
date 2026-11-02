/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;

import android.view.ViewGroup;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.ui.Components.RecyclerListView;
import java.util.ArrayList;
import java.util.List;

/** One RecyclerView; isolated inner holders preserve original local types for legacy casts. */
public final class NativeSectionsAdapter extends RecyclerListView.SelectionAdapter {
    private final List<Part> parts = new ArrayList<>();
    private static final int TYPE_STRIDE = 4096;
    private boolean closed;
    private final class Part {
        final NativeSettingsSection owner;
        final RecyclerListView.SelectionAdapter adapter;
        final RecyclerView.AdapterDataObserver observer;
        int count;
        Part(NativeSettingsSection owner, RecyclerListView.SelectionAdapter adapter) {
            this.owner=owner;this.adapter=adapter;count=adapter.getItemCount();
            observer=new RecyclerView.AdapterDataObserver(){
                @Override public void onChanged(){
                    if(closed)return;int offset=offset(Part.this),old=count,next=adapter.getItemCount();count=next;
                    int common=Math.min(old,next);
                    if(common>0)notifyItemRangeChanged(offset,common);
                    if(next>old)notifyItemRangeInserted(offset+old,next-old);
                    else if(old>next)notifyItemRangeRemoved(offset+next,old-next);
                }
                @Override public void onItemRangeChanged(int start,int size,Object payload){if(!closed)notifyItemRangeChanged(offset(Part.this)+start,size,payload);}
                @Override public void onItemRangeChanged(int start,int size){onItemRangeChanged(start,size,null);}
                @Override public void onItemRangeInserted(int start,int size){if(!closed){count+=size;notifyItemRangeInserted(offset(Part.this)+start,size);}}
                @Override public void onItemRangeRemoved(int start,int size){if(!closed){count-=size;notifyItemRangeRemoved(offset(Part.this)+start,size);}}
                @Override public void onItemRangeMoved(int from,int to,int size){if(!closed){if(size==1)notifyItemMoved(offset(Part.this)+from,offset(Part.this)+to);else onChanged();}}
            };
            adapter.registerAdapterDataObserver(observer);
        }
    }
    private static final class Wrapped extends RecyclerListView.Holder {
        final RecyclerView.ViewHolder inner;
        final int part;
        int local=-1;
        Wrapped(RecyclerView.ViewHolder inner,int part){super(inner.itemView);this.inner=inner;this.part=part;}
    }
    public void add(NativeSettingsSection section,RecyclerListView.SelectionAdapter adapter){
        Part part=new Part(section,adapter);parts.add(part);
        if(section instanceof tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity)
            ((tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity)section).setSettings3Position(local->offset(part)+local);
        if(section instanceof tw.nekomimi.nekogram.settings.BaseNekoXSettingsActivity)
            ((tw.nekomimi.nekogram.settings.BaseNekoXSettingsActivity)section).setSettings3Position(local->offset(part)+local);
    }
    private int offset(Part target){int offset=0;for(Part p:parts){if(p==target)return offset;offset+=p.count;}throw new IllegalStateException("Detached section");}
    private int index(int position){for(int i=0;i<parts.size();i++){if(position<parts.get(i).count)return i;position-=parts.get(i).count;}throw new IndexOutOfBoundsException();}
    private int local(int global,int part){for(int i=0;i<part;i++)global-=parts.get(i).count;return global;}
    @Override public int getItemCount(){int count=0;for(Part p:parts)count+=p.count;return count;}
    @Override public int getItemViewType(int position){int part=index(position),type=parts.get(part).adapter.getItemViewType(local(position,part));if(type<0||type>=TYPE_STRIDE)throw new IllegalStateException("Unsupported native settings view type");return part*TYPE_STRIDE+type;}
    @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){int part=type/TYPE_STRIDE;return new Wrapped(parts.get(part).adapter.createViewHolder(parent,type%TYPE_STRIDE),part);}
    @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position){if(closed)return;Wrapped w=(Wrapped)holder;w.local=local(position,w.part);parts.get(w.part).adapter.bindViewHolder(w.inner,w.local);}
    @Override public boolean isEnabled(RecyclerView.ViewHolder holder){if(closed)return false;Wrapped w=(Wrapped)holder;int absolute=holder.getAdapterPosition();int position=absolute<0?w.local:local(absolute,w.part);return position>=0&&position<parts.get(w.part).count&&parts.get(w.part).owner.settings3Enabled(position,w.inner);}
    public void click(View view,int position,float x,float y){if(closed||position<0||position>=getItemCount())return;int part=index(position);parts.get(part).owner.settings3Click(view,local(position,part),x,y);}
    public boolean longClick(View view,int position,float x,float y){if(closed||position<0||position>=getItemCount())return false;int part=index(position);return parts.get(part).owner.settings3LongClick(view,local(position,part),x,y);}
    @Override public void onViewAttachedToWindow(RecyclerView.ViewHolder holder){if(closed)return;Wrapped w=(Wrapped)holder;parts.get(w.part).adapter.onViewAttachedToWindow(w.inner);}
    @Override public void onViewDetachedFromWindow(RecyclerView.ViewHolder holder){if(closed)return;Wrapped w=(Wrapped)holder;parts.get(w.part).adapter.onViewDetachedFromWindow(w.inner);}
    @Override public void onViewRecycled(RecyclerView.ViewHolder holder){if(closed)return;Wrapped w=(Wrapped)holder;parts.get(w.part).adapter.onViewRecycled(w.inner);w.local=-1;}
    public void close(){if(closed)return;closed=true;for(Part p:parts)p.adapter.unregisterAdapterDataObserver(p.observer);parts.clear();}
}
