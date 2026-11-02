/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Bounded, RAM only. Keys include exact rendered text + excluded ranges + message scope. */
public final class InlineConversionCache {
    public static final int CAPACITY=32;
    private final Map<String,List<InlineConversionMatch>> entries=new LinkedHashMap<String,List<InlineConversionMatch>>(CAPACITY,.75f,true){
        @Override protected boolean removeEldestEntry(Map.Entry<String,List<InlineConversionMatch>> e){return size()>CAPACITY;}
    };
    public synchronized List<InlineConversionMatch> get(String key){return entries.get(key);}
    public synchronized void put(String key,List<InlineConversionMatch> value){entries.put(key,value);}
    public synchronized void clear(){entries.clear();}
    public synchronized int size(){return entries.size();}
}
