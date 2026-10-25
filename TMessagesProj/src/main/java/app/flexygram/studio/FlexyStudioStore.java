/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.AtomicFile;
import app.flexygram.bubbles.BubbleConfig;
import app.flexygram.header.HeaderConfig;
import app.flexygram.composer.FlexyComposerConfig;
import app.flexygram.studio.core.*;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.Utilities;
import org.telegram.ui.ChatActivity;
import org.telegram.ui.LaunchActivity;
import org.telegram.ui.LauncherIconController;
import java.io.*;
import java.lang.ref.WeakReference;
import java.util.*;

/** Only explicit Studio operations use globalQueue. No dedicated thread or idle observer. */
public final class FlexyStudioStore {
    public interface Completion {void done(boolean ok,boolean recoveryPending,StudioTransaction.Receipt receipt);}
    private static volatile boolean applying;
    private static final List<WeakReference<Runnable>> deferred=new ArrayList<>();
    private static StudioTransaction.Receipt last;
    private static boolean recovering;
    private FlexyStudioStore(){}
    private static Context context(){return ApplicationLoader.applicationContext;}
    private static SharedPreferences prefs(String name){return context().getSharedPreferences(name,Context.MODE_PRIVATE);}
    public static boolean deferComposer(Runnable refresh) {
        if(!applying)return false;
        for(WeakReference<Runnable> r:deferred)if(r.get()==refresh)return true;
        deferred.add(new WeakReference<>(refresh));return true;
    }
    public static Map<String,Map<String,Object>> snapshot() {
        Map<String,Map<String,Object>> result=new TreeMap<>();
        for(StudioSchema.Key key:StudioSchema.keys()) {
            Object value;
            if(key.section.equals("icon"))value=activeIcon();
            else if(key.section.equals("header")&&key.id.equals("style")&&!prefs(key.file).contains(key.preference)) {
                SharedPreferences old=app.exteraless.appearance.AppearanceConfig.getPreferences();
                boolean legacy=old.getBoolean("OEAppearanceIosChatHeaderAuto",false)||old.getBoolean("OEAppearanceIosChatHeader",true);
                value=legacy?0:1;
            } else value=readPreference(prefs(key.file),key);
            value=StudioSchema.value(key,value);
            result.computeIfAbsent(key.section,k->new TreeMap<>()).put(key.id,value);
        }
        return result;
    }
    private static Object readPreference(SharedPreferences p,StudioSchema.Key key) {
        if(key.defaultValue instanceof Boolean)return p.getBoolean(key.preference,(Boolean)key.defaultValue);
        if(key.defaultValue instanceof Integer)return p.getInt(key.preference,(Integer)key.defaultValue);
        return p.getString(key.preference,(String)key.defaultValue);
    }
    private static String activeIcon() {
        for(LauncherIconController.LauncherIcon icon:LauncherIconController.LauncherIcon.values())if(LauncherIconController.isEnabled(icon))return icon.name();
        return "EXTERALESS";
    }
    public static boolean apply(StudioCodec.Preset preset,Completion completion) {
        if(applying)return false;applying=true;
        Utilities.globalQueue.postRunnable(()->{
            StudioTransaction.Receipt receipt=null;boolean ok=false,pending=false;
            Set<String> affected=new HashSet<>(preset.sections.keySet());
            try { affected.addAll(recoverOnWorker());receipt=StudioTransaction.apply(new Backend(),preset);last=receipt;ok=true; }
            catch(Exception failure){pending=hasJournal();}
            final boolean success=ok,recovery=pending;final StudioTransaction.Receipt result=receipt;
            AndroidUtilities.runOnUIThread(()->{finish(affected);completion.done(success,recovery,result);});
        });return true;
    }
    public static boolean undo(StudioTransaction.Receipt receipt,Completion completion) {
        if(applying||receipt==null||last!=receipt)return false;applying=true;
        Utilities.globalQueue.postRunnable(()->{
            Set<String> sections=new HashSet<>();for(StudioSchema.Key k:receipt.before.keySet())sections.add(k.section);
            boolean ok=false;
            try{sections.addAll(recoverOnWorker());StudioTransaction.undo(new Backend(),receipt);last=null;ok=true;}catch(Exception ignored){}
            final boolean success=ok,pending=hasJournal();
            AndroidUtilities.runOnUIThread(()->{finish(sections);completion.done(success,pending,null);});
        });return true;
    }
    private static void finish(Set<String> sections) {
        applying=false;
        if(sections.contains("bubbles"))BubbleConfig.load();
        if(sections.contains("header"))HeaderConfig.load();
        List<WeakReference<Runnable>> notify=new ArrayList<>(deferred);deferred.clear();
        for(WeakReference<Runnable> r:notify){Runnable action=r.get();if(action!=null)action.run();}
        if(LaunchActivity.getSafeLastFragment() instanceof ChatActivity)((ChatActivity)LaunchActivity.getSafeLastFragment()).onFlexyStudioApplied(sections);
    }
    private static AtomicFile journal(){return new AtomicFile(new File(context().getFilesDir(),"flexystudio-rollback.dat"));}
    /** One cheap startup existence check; disk recovery is scheduled only after an interrupted import. */
    public static void recoverIfNeeded() {
        if(recovering||applying||!hasJournal())return;recovering=true;applying=true;
        Utilities.globalQueue.postRunnable(()->{
            Set<String> affected=new HashSet<>();
            try{Map<StudioSchema.Key,StudioTransaction.Slot> saved=readJournal();for(StudioSchema.Key k:saved.keySet())affected.add(k.section);StudioTransaction.recover(new Backend(),saved);}catch(Exception ignored){}
            AndroidUtilities.runOnUIThread(()->{recovering=false;finish(affected);});
        });
    }
    private static Set<String> recoverOnWorker()throws Exception {
        Set<String> affected=new HashSet<>();
        if(hasJournal()){Map<StudioSchema.Key,StudioTransaction.Slot> saved=readJournal();for(StudioSchema.Key key:saved.keySet())affected.add(key.section);StudioTransaction.recover(new Backend(),saved);}
        return affected;
    }
    private static boolean hasJournal(){File base=journal().getBaseFile();return base.exists()||new File(base.getPath()+".bak").exists();}
    private static Map<StudioSchema.Key,StudioTransaction.Slot> readJournal()throws Exception {
        try(FileInputStream stream=journal().openRead();DataInputStream in=new DataInputStream(stream)) {
            if(stream.getChannel().size()>16384)throw new IOException("journal");
            if(in.readInt()!=0x46534731)throw new IOException("journal");int n=in.readInt();if(n<1||n>StudioSchema.MAX_KEYS)throw new IOException("journal");
            Map<StudioSchema.Key,StudioTransaction.Slot> result=new LinkedHashMap<>();
            for(int i=0;i<n;i++) {
                StudioSchema.Key k=StudioSchema.key(in.readUTF(),in.readUTF());boolean present=in.readBoolean();
                Object value=k.defaultValue instanceof Boolean?in.readBoolean():k.defaultValue instanceof Integer?in.readInt():in.readUTF();
                if(result.put(k,new StudioTransaction.Slot(present,StudioSchema.value(k,value)))!=null)throw new IOException("journal");
            }
            if(in.read()!=-1)throw new IOException("journal");return result;
        }
    }
    private static final class Backend implements StudioTransaction.Backend {
        public StudioTransaction.Slot read(StudioSchema.Key key) {
            SharedPreferences p=prefs(key.file);boolean present=p.contains(key.preference);
            Object value=key.section.equals("icon")?activeIcon():readPreference(p,key);
            if(value==null)value=key.defaultValue;
            return new StudioTransaction.Slot(present,StudioSchema.value(key,value));
        }
        public void write(String file,Map<StudioSchema.Key,StudioTransaction.Slot> values)throws Exception {
            SharedPreferences.Editor editor=prefs(file).edit();
            for(Map.Entry<StudioSchema.Key,StudioTransaction.Slot> entry:values.entrySet()) {
                StudioSchema.Key k=entry.getKey();StudioTransaction.Slot slot=entry.getValue();Object v=StudioSchema.value(k,slot.value);
                if(k.section.equals("icon"))LauncherIconController.setIcon(LauncherIconController.LauncherIcon.valueOf((String)v));
                if(!slot.present)editor.remove(k.preference);
                else if(v instanceof Boolean)editor.putBoolean(k.preference,(Boolean)v);
                else if(v instanceof Integer)editor.putInt(k.preference,(Integer)v);
                else editor.putString(k.preference,(String)v);
            }
            if(!editor.commit())throw new IOException("preferences");
        }
        public void journal(Map<StudioSchema.Key,StudioTransaction.Slot> before)throws Exception {
            AtomicFile file=FlexyStudioStore.journal();FileOutputStream stream=file.startWrite();
            try {
                DataOutputStream out=new DataOutputStream(stream);out.writeInt(0x46534731);out.writeInt(before.size());
                for(Map.Entry<StudioSchema.Key,StudioTransaction.Slot> entry:before.entrySet()) {
                    StudioSchema.Key k=entry.getKey();Object v=entry.getValue().value;
                    out.writeUTF(k.section);out.writeUTF(k.id);out.writeBoolean(entry.getValue().present);
                    if(v instanceof Boolean)out.writeBoolean((Boolean)v);else if(v instanceof Integer)out.writeInt((Integer)v);else out.writeUTF((String)v);
                }
                out.flush();file.finishWrite(stream);
            }catch(Exception failed){file.failWrite(stream);throw failed;}
        }
        public void clearJournal()throws IOException {AtomicFile file=FlexyStudioStore.journal();file.delete();if(hasJournal())throw new IOException("journal");}
    }
}
