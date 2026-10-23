package app.flexygram.composer;

import static org.telegram.messenger.LocaleController.getString;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Cells.TextSettingsCell;
import tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity;

public final class FlexyComposerSettingsActivity extends BaseNekoSettingsActivity {
    private int styleRow, glassRow, infoRow;

    @Override protected void updateRows() {
        super.updateRows();
        styleRow = addRow("flexyComposerStyle");
        glassRow = addRow("flexyComposerGlass");
        infoRow = addRow();
    }
    @Override protected String getActionBarTitle() { return getString(R.string.FlexyComposerSettings); }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position == styleRow) {
            showDialog(new AlertDialog.Builder(getParentActivity(), getResourceProvider())
                .setTitle(getString(R.string.FlexyComposerStyle))
                .setItems(new CharSequence[]{getString(R.string.FlexyComposerClassic), getString(R.string.FlexyComposerCompact)}, (dialog, which) -> {
                    FlexyComposerConfig.setStyle(which);
                    listAdapter.notifyItemChanged(styleRow);
                    listAdapter.notifyItemChanged(glassRow);
                }).create());
        } else if (position == glassRow && FlexyComposerConfig.compact()) {
            FlexyComposerConfig.setGlass(!FlexyComposerConfig.glass());
            listAdapter.notifyItemChanged(glassRow);
        }
    }
    private final class Adapter extends BaseListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) {
            return position == styleRow ? TYPE_SETTINGS : position == glassRow ? TYPE_CHECK : TYPE_INFO_PRIVACY;
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            if (position == styleRow) {
                ((TextSettingsCell)holder.itemView).setTextAndValue(getString(R.string.FlexyComposerStyle),
                    getString(FlexyComposerConfig.compact() ? R.string.FlexyComposerCompact : R.string.FlexyComposerClassic), true);
            } else if (position == glassRow) {
                TextCheckCell cell = (TextCheckCell)holder.itemView;
                cell.setTextAndCheck(getString(R.string.FlexyComposerGlass), FlexyComposerConfig.glass(), false);
                cell.setEnabled(FlexyComposerConfig.compact(), null);
            } else {
                ((TextInfoPrivacyCell)holder.itemView).setText(getString(R.string.FlexyComposerInfo));
            }
        }
    }
}
