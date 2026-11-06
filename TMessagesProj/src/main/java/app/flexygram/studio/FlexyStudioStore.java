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

/** All transfer, comparison and transaction I/O shares the bounded Studio worker. */
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
        return Collections.singletonMap("client", Collections.singletonMap("settings", StudioClientBackup.snapshot()));
    }
    public static void validate(StudioCodec.Preset preset) {
        if(preset.sections.containsKey("client"))StudioClientBackup.validate((String)preset.sections.get("client").get("settings"));
    }

    static Object readPreference(SharedPreferences p,StudioSchema.Key key) {
        if(key.defaultValue instanceof Boolean)return p.getBoolean(key.preference,(Boolean)key.defaultValue);
        if(key.defaultValue instanceof Integer)return p.getInt(key.preference,(Integer)key.defaultValue);
        return p.getString(key.preference,(String)key.defaultValue);
    }
    private static String activeIcon() {
        for(LauncherIconController.LauncherIcon icon:LauncherIconController.LauncherIcon.values())if(LauncherIconController.isEnabled(icon))return icon.name();
        return "EXTERALESS";
    }
    public static boolean apply(StudioCodec.Preset preset,Completion completion) {
        return applyPrepared(()->preset,completion);
    }
    static boolean applySelection(StudioImportPlan plan,Set<String> selected,Completion completion) {
        Set<String> included=new HashSet<>(selected);
        return applyPrepared(()->plan.select(included),completion);
    }
    private static boolean applyPrepared(java.util.concurrent.Callable<StudioCodec.Preset> source,Completion completion) {
        if(applying)return false;applying=true;
        try{FlexyStudioIO.execute(()->{
            StudioTransaction.Receipt receipt=null;boolean ok=false,pending=false;
            Set<String> affected=new HashSet<>();
            try { StudioCodec.Preset preset=source.call();validate(preset);affected.addAll(preset.sections.keySet());affected.addAll(recoverOnWorker());receipt=StudioTransaction.apply(new Backend(),preset);last=receipt;ok=true; }
            catch(Exception failure){pending=hasJournal();}
            final boolean success=ok,recovery=pending;final StudioTransaction.Receipt result=receipt;
            AndroidUtilities.runOnUIThread(()->{finish(affected);completion.done(success,recovery,result);});
        });return true;}catch(java.util.concurrent.RejectedExecutionException busy){applying=false;return false;}
    }
    public static boolean undo(StudioTransaction.Receipt receipt,Completion completion) {
        if(applying||receipt==null||last!=receipt)return false;applying=true;
        try{FlexyStudioIO.execute(()->{
            Set<String> sections=new HashSet<>();for(StudioSchema.Key k:receipt.before.keySet())sections.add(k.section);
            boolean ok=false;
            try{sections.addAll(recoverOnWorker());StudioTransaction.undo(new Backend(),receipt);last=null;ok=true;}catch(Exception ignored){}
            final boolean success=ok,pending=hasJournal();
            AndroidUtilities.runOnUIThread(()->{finish(sections);completion.done(success,pending,null);});
        });return true;}catch(java.util.concurrent.RejectedExecutionException busy){applying=false;return false;}
    }
    private static void finish(Set<String> sections) {
        applying=false;
        if(sections.contains("client")) {
            sections.addAll(Arrays.asList("bubbles","header","composer","icon"));
            org.telegram.ui.ActionBar.BaseFragment top=LaunchActivity.getSafeLastFragment();
            if(top!=null && top.getParentLayout()!=null)top.getParentLayout().rebuildFragments(0);
        }
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
        try{FlexyStudioIO.execute(()->{
            Set<String> affected=new HashSet<>();
            try{Map<StudioSchema.Key,StudioTransaction.Slot> saved=readJournal();for(StudioSchema.Key k:saved.keySet())affected.add(k.section);StudioTransaction.recover(new Backend(),saved);}catch(Exception ignored){}
            AndroidUtilities.runOnUIThread(()->{recovering=false;finish(affected);});
        });}catch(java.util.concurrent.RejectedExecutionException busy){recovering=false;applying=false;}
    }
    private static Set<String> recoverOnWorker()throws Exception {
        Set<String> affected=new HashSet<>();
        if(hasJournal()){Map<StudioSchema.Key,StudioTransaction.Slot> saved=readJournal();for(StudioSchema.Key key:saved.keySet())affected.add(key.section);StudioTransaction.recover(new Backend(),saved);}
        return affected;
    }
    private static boolean hasJournal(){File base=journal().getBaseFile();return base.exists()||new File(base.getPath()+".bak").exists();}
    private static Map<StudioSchema.Key,StudioTransaction.Slot> readJournal()throws Exception {
        try(FileInputStream stream=journal().openRead();DataInputStream in=new DataInputStream(stream)) {
            return StudioJournal.read(stream,stream.getChannel().size());
        }
    }
    private static final class Backend implements StudioTransaction.Backend {
        public StudioTransaction.Slot readForChange(StudioSchema.Key key,StudioTransaction.Slot scope) {
            if(key.section.equals("client"))return new StudioTransaction.Slot(true,StudioClientBackup.snapshotLike((String)scope.value));
            return read(key);
        }
        public StudioTransaction.Slot read(StudioSchema.Key key) {
            if(key.section.equals("client"))return new StudioTransaction.Slot(true,StudioClientBackup.snapshot());
            SharedPreferences p=prefs(key.file);boolean present=p.contains(key.preference);
            Object value=key.section.equals("icon")?activeIcon():readPreference(p,key);
            if(value==null)value=key.defaultValue;
            return new StudioTransaction.Slot(present,StudioSchema.value(key,value));
        }
        public void write(String file,Map<StudioSchema.Key,StudioTransaction.Slot> values)throws Exception {
            if(file.equals("@client")) { StudioClientBackup.apply((String)values.get(StudioSchema.key("client","settings")).value); return; }
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
                StudioJournal.write(stream,before);file.finishWrite(stream);
            }catch(Exception failed){file.failWrite(stream);throw failed;}
        }
        public void clearJournal()throws IOException {AtomicFile file=FlexyStudioStore.journal();file.delete();if(hasJournal())throw new IOException("journal");}
    }
}
