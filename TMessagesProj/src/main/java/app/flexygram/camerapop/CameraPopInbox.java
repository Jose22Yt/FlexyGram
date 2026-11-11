/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Set;

/** Only IDs/counters. Stable order and recycled UI rows; no message bodies. UI thread. */
public final class CameraPopInbox {
    public static final class Row {
        public final long dialog;
        public final int unread;
        public Row(long dialog,int unread) {this.dialog=dialog;this.unread=unread;}
    }
    private final LinkedHashMap<Long,Row> rows=new LinkedHashMap<>();
    private long revision;
    public void update(long dialog,int unread,boolean recent) {
        Row old=rows.get(dialog);
        if(unread<=0) {if(rows.remove(dialog)!=null)revision++;return;}
        if(old!=null && old.unread==unread && !recent)return;
        if(recent)rows.remove(dialog);
        rows.put(dialog,new Row(dialog,unread));revision++;
    }
    public void retain(Set<Long> visible) {if(rows.keySet().retainAll(visible))revision++;}
    public List<Row> snapshot() {
        ArrayList<Row> result=new ArrayList<>(rows.values());Collections.reverse(result);return result;
    }
    public int total() {long total=0;for(Row row:rows.values())total+=row.unread;return (int)Math.min(Integer.MAX_VALUE,total);}
    public int size() {return rows.size();}
    public long newest() {long id=0;for(long dialog:rows.keySet())id=dialog;return id;}
    public long revision() {return revision;}
    public void clear() {if(!rows.isEmpty()){rows.clear();revision++;}}
}
