package app.flexygram.studio;

import app.flexygram.studio.core.*;
import android.content.Context;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.ui.LauncherIconController;
import java.util.*;

/** Worker-only comparison and subset construction. Preparing a plan never writes preferences. */
public final class StudioImportPlan {
    static final class Change {
        final String file,key; final Object before,after;
        Change(String file,String key,Object before,Object after){this.file=file;this.key=key;this.before=before;this.after=after;}
    }
    static final class Group {
        final String id; final List<Change> changes;
        Group(String id,List<Change> changes){this.id=id;this.changes=Collections.unmodifiableList(new ArrayList<>(changes));}
    }
    final List<Group> groups;
    private final StudioCodec.Preset preset;
    private final boolean client;
    private StudioImportPlan(StudioCodec.Preset preset,Map<String,List<Change>> changes) {
        this.preset=preset;client=preset.sections.containsKey("client");
        List<Group> result=new ArrayList<>();
        for(Map.Entry<String,List<Change>> group:changes.entrySet())result.add(new Group(group.getKey(),group.getValue()));
        groups=Collections.unmodifiableList(result);
    }
    private static Map<String,Object> object(Object value){return StudioClientBackup.object(value);}
    private static void add(Map<String,List<Change>> groups,String id,String file,String key,Object before,Object after){
        List<Change> changes=groups.computeIfAbsent(id,k->new ArrayList<>());
        if(!Objects.equals(before,after))changes.add(new Change(file,key,before,after));
    }
    public static StudioImportPlan prepare(StudioCodec.Preset preset) {
        FlexyStudioStore.validate(preset);
        Map<String,List<Change>> groups=new TreeMap<>();
        if(preset.sections.containsKey("client")) {
            String encoded=(String)preset.sections.get("client").get("settings");
            Map<String,Object> incoming=object(StudioCodec.decodeValues(encoded));
            Map<String,Object> current=object(StudioCodec.decodeValues(StudioClientBackup.snapshotLike(encoded)));
            StudioClientCatalog catalog=new StudioClientCatalog();
            for(Map.Entry<String,Object> file:object(incoming.get("files")).entrySet()) {
                Map<String,Object> old=object(object(current.get("files")).get(file.getKey()));
                for(Map.Entry<String,Object> setting:object(file.getValue()).entrySet()) {
                    String section=catalog.files().get(file.getKey()).get(setting.getKey()).section;
                    add(groups,section,file.getKey(),setting.getKey(),old.get(setting.getKey()),setting.getValue());
                }
            }
            for(String id:Arrays.asList("theme","icon"))if(incoming.containsKey(id))add(groups,id,"@client",id,current.get(id),incoming.get(id));
        } else {
            for(Map.Entry<String,Map<String,Object>> section:preset.sections.entrySet())for(Map.Entry<String,Object> setting:section.getValue().entrySet()) {
                StudioSchema.Key key=StudioSchema.key(section.getKey(),setting.getKey());
                Object old;
                if(section.getKey().equals("icon")) {
                    old="EXTERALESS";
                    for(LauncherIconController.LauncherIcon icon:LauncherIconController.LauncherIcon.values())if(LauncherIconController.isEnabled(icon)){old=icon.name();break;}
                } else old=FlexyStudioStore.readPreference(ApplicationLoader.applicationContext.getSharedPreferences(key.file,Context.MODE_PRIVATE),key);
                add(groups,section.getKey(),key.file,setting.getKey(),old,setting.getValue());
            }
        }
        return new StudioImportPlan(preset,groups);
    }
    Set<String> changedGroups(){Set<String> result=new LinkedHashSet<>();for(Group group:groups)if(!group.changes.isEmpty())result.add(group.id);return result;}
    StudioCodec.Preset select(Set<String> selected) {
        if(selected.isEmpty()||!changedGroups().containsAll(selected))throw new IllegalArgumentException("selection");
        if(!client) {
            Map<String,Map<String,Object>> result=new TreeMap<>();
            for(Group group:groups)if(selected.contains(group.id))for(Change change:group.changes)result.computeIfAbsent(group.id,k->new TreeMap<>()).put(change.key,change.after);
            return StudioCodec.create(preset.name,result);
        }
        Map<String,Object> root=new TreeMap<>(),files=new TreeMap<>();root.put("version",1);root.put("files",files);
        for(Group group:groups)if(selected.contains(group.id))for(Change change:group.changes) {
            if(change.file.equals("@client"))root.put(change.key,change.after);
            else {
                Map<String,Object> settings=(Map<String,Object>)files.computeIfAbsent(change.file,k->new TreeMap<>());
                settings.put(change.key,change.after);
            }
        }
        return StudioCodec.create(preset.name,Collections.singletonMap("client",Collections.singletonMap("settings",StudioCodec.encodeValues(root))));
    }
}
