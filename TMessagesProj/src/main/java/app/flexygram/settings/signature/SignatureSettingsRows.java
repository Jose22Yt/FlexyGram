/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import java.util.*;
import java.util.function.Predicate;
import tw.nekomimi.nekogram.config.cell.*;
/** Keeps native conditional insertions inside their canonical page, including after callbacks. */
public final class SignatureSettingsRows extends ArrayList<AbstractConfigCell> {
    private final Predicate<AbstractConfigCell> allowed;
    public SignatureSettingsRows(Collection<AbstractConfigCell> original,Predicate<AbstractConfigCell> allowed){this.allowed=allowed;addAll(original);pruneEmptyGroups();}
    @Override public boolean add(AbstractConfigCell c){return allowed.test(c)&&super.add(c);}
    @Override public void add(int index,AbstractConfigCell c){if(allowed.test(c))super.add(index,c);}
    @Override public boolean addAll(Collection<? extends AbstractConfigCell> c){boolean changed=false;for(AbstractConfigCell v:c)changed|=add(v);return changed;}
    @Override public boolean addAll(int index,Collection<? extends AbstractConfigCell> c){int start=index;for(AbstractConfigCell v:c)if(allowed.test(v))super.add(index++,v);return index!=start;}
    private void pruneEmptyGroups(){
        // Preserve a final native divider: CellGroup.needSetDivider looks at the following item.
        for(int i=size()-1;i>=0;i--){AbstractConfigCell cell=get(i);if(cell instanceof ConfigCellHeader){int end=i+1;while(end<size()&&!(get(end)instanceof ConfigCellHeader)&&!(get(end)instanceof ConfigCellDivider))end++;if(end==i+1){remove(i);if(i<size()&&get(i)instanceof ConfigCellDivider)remove(i);}}}
        while(!isEmpty()&&get(0)instanceof ConfigCellDivider)remove(0);
    }
}
