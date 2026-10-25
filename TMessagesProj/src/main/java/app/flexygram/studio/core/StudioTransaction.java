/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio.core;

import java.util.*;

/** Grouped writes with checked rollback. Backend owns durability and native icon side effects. */
public final class StudioTransaction {
    public static final class Slot {
        public final boolean present;
        public final Object value;
        public Slot(boolean present,Object value){this.present=present;this.value=value;}
        @Override public boolean equals(Object other){return other instanceof Slot&&present==((Slot)other).present&&Objects.equals(value,((Slot)other).value);}
        @Override public int hashCode(){return Objects.hash(present,value);}
    }
    public interface Backend {
        Slot read(StudioSchema.Key key)throws Exception;
        void write(String file,Map<StudioSchema.Key,Slot> values)throws Exception;
        void journal(Map<StudioSchema.Key,Slot> before)throws Exception;
        void clearJournal()throws Exception;
    }
    public static final class Receipt {
        public final Map<StudioSchema.Key,Slot> before,after;
        private Receipt(Map<StudioSchema.Key,Slot> before,Map<StudioSchema.Key,Slot> after) {
            this.before=Collections.unmodifiableMap(new LinkedHashMap<>(before));this.after=Collections.unmodifiableMap(new LinkedHashMap<>(after));
        }
    }
    public static final class Failure extends Exception {
        public final boolean rollbackFailed;
        Failure(boolean rollbackFailed){super("apply_failed");this.rollbackFailed=rollbackFailed;}
    }
    private StudioTransaction(){}
    public static Receipt apply(Backend backend,StudioCodec.Preset preset)throws Exception {
        Map<StudioSchema.Key,Slot> after=new LinkedHashMap<>();
        for(String section:preset.sections.keySet())for(Map.Entry<String,Object> value:preset.sections.get(section).entrySet()) {
            StudioSchema.Key key=StudioSchema.key(section,value.getKey());after.put(key,new Slot(true,value.getValue()));
        }
        return change(backend,after);
    }
    public static void undo(Backend backend,Receipt receipt)throws Exception {
        // Do not silently overwrite settings the owner changed after the import.
        for(StudioSchema.Key key:receipt.after.keySet())if(!receipt.after.get(key).equals(backend.read(key)))throw new IllegalStateException("undo_conflict");
        change(backend,receipt.before);
    }
    private static Receipt change(Backend backend,Map<StudioSchema.Key,Slot> after)throws Exception {
        Map<StudioSchema.Key,Slot> before=new LinkedHashMap<>();
        for(StudioSchema.Key key:after.keySet())before.put(key,backend.read(key));
        backend.journal(before);
        try { write(backend,after);backend.clearJournal();return new Receipt(before,after); }
        catch(Exception failed) {
            boolean rollbackFailed=false;
            try{write(backend,before);backend.clearJournal();}catch(Exception restoreFailed){rollbackFailed=true;}
            throw new Failure(rollbackFailed);
        }
    }
    public static void recover(Backend backend,Map<StudioSchema.Key,Slot> before)throws Exception {write(backend,before);backend.clearJournal();}
    private static void write(Backend backend,Map<StudioSchema.Key,Slot> changes)throws Exception {
        Map<String,Map<StudioSchema.Key,Slot>> grouped=new LinkedHashMap<>();
        for(Map.Entry<StudioSchema.Key,Slot> entry:changes.entrySet())grouped.computeIfAbsent(entry.getKey().file,k->new LinkedHashMap<>()).put(entry.getKey(),entry.getValue());
        for(Map.Entry<String,Map<StudioSchema.Key,Slot>> group:grouped.entrySet())backend.write(group.getKey(),group.getValue());
    }
}
