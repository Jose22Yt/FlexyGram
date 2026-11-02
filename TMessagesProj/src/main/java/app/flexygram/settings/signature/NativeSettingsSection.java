/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.Components.RecyclerListView;
/** An existing controller contributes rows, never a nested scroll view or navigation stack. */
public interface NativeSettingsSection {
    RecyclerListView.SelectionAdapter prepareSettings3(BaseFragment host, RecyclerListView list);
    void settings3Click(View view,int position,float x,float y);
    boolean settings3LongClick(View view,int position,float x,float y);
    boolean settings3Enabled(int position,RecyclerView.ViewHolder holder);
    BaseFragment settings3Controller();
    void releaseSettings3();
}
