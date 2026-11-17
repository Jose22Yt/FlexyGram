package app.flexygram.kyant;

import android.content.Context;
import android.os.Build;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;

/** Optional material only. No navigation destinations or Telegram flags are changed. */
public final class KyantDockSettingsActivity extends SignatureMatteSettingsActivity {
    private int toggleRow, infoRow;
    @Override protected String getActionBarTitle() { return LocaleController.getString(R.string.CompactTabs); }
    @Override protected String getKey() { return "flexy_kyant_dock"; }
    @Override public int getSearchGuid() { return 11_200_000; }
    @Override public int getSearchIcon() { return R.drawable.fg_dm_barra_inferior; }
    @Override public String getSearchPrefix() { return "Flexy"; }
    @Override protected void updateRows() {
        super.updateRows();
        toggleRow = addRow("kyantHomeDock"); infoRow = addRow("kyantHomeDockInfo");
    }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position == toggleRow && Build.VERSION.SDK_INT >= 33) {
            KyantDockConfig.setEnabled(!KyantDockConfig.isEnabled());
            if (listAdapter != null) listAdapter.notifyItemChanged(toggleRow);
        }
    }
    @Override protected BaseListAdapter createAdapter(Context context) {
        return new MatteListAdapter(context) {
            @Override public int getItemViewType(int p) { return p == toggleRow ? TYPE_CHECK : TYPE_INFO_PRIVACY; }
            @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int p, boolean partial) {
                if (p == toggleRow) {
                    TextCheckCell cell = (TextCheckCell) holder.itemView;
                    cell.setTextAndValueAndCheck(LocaleController.getString(R.string.FlexyKyantDock),
                            LocaleController.getString(R.string.FlexyKyantDockSubtitle), KyantDockConfig.isEnabled(), true, false);
                    cell.setEnabled(Build.VERSION.SDK_INT >= 33);
                } else ((TextInfoPrivacyCell) holder.itemView).setText(LocaleController.getString(R.string.FlexyKyantDockInfo));
            }
        };
    }
}
