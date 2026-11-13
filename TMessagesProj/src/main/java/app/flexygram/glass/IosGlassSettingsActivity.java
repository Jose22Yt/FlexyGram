/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.glass;

import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;

/** Compact controls for one replacing material; no legacy preferences are rewritten. */
public final class IosGlassSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int[] SURFACES = {0, IosGlassConfig.HOME, IosGlassConfig.COMPOSER, IosGlassConfig.HEADER, IosGlassConfig.FOLDERS};
    private static final int[] TITLES = {R.string.FlexyIosGlassEnable, R.string.FlexyIosGlassHome,
            R.string.FlexyIosGlassComposer, R.string.FlexyIosGlassHeader, R.string.FlexyIosGlassFolders};
    @Override protected String getActionBarTitle() { return LocaleController.getString(R.string.FlexyIosGlassTitle); }
    @Override protected void updateRows() {
        super.updateRows();
        for (int i = 0; i < TITLES.length; i++) addRow("iosGlass" + i);
        addRow("iosGlassInfo");
    }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position < 0 || position >= SURFACES.length) return;
        if (position == 0) {
            if (!IosGlassConfig.supported() && !IosGlassConfig.enabled()) return;
            IosGlassConfig.setEnabled(!IosGlassConfig.enabled());
        } else IosGlassConfig.setSelected(SURFACES[position], !IosGlassConfig.selected(SURFACES[position]));
        listAdapter.notifyItemChanged(position);
    }
    @Override protected BaseListAdapter createAdapter(Context context) {
        return new MatteListAdapter(context) {
            @Override public int getItemViewType(int position) { return position < TITLES.length ? TYPE_CHECK : TYPE_INFO_PRIVACY; }
            @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
                if (position < TITLES.length) {
                    TextCheckCell cell = (TextCheckCell)holder.itemView;
                    cell.setTextAndCheck(LocaleController.getString(TITLES[position]),
                            position == 0 ? IosGlassConfig.enabled() : IosGlassConfig.selected(SURFACES[position]),
                            position + 1 < TITLES.length);
                    cell.setAlpha(position == 0 && !IosGlassConfig.supported() && !IosGlassConfig.enabled() ? .5f : 1f);
                } else ((TextInfoPrivacyCell)holder.itemView).setText(LocaleController.getString(
                        IosGlassConfig.supported() ? R.string.FlexyIosGlassInfo : R.string.FlexyIosGlassUnsupported));
            }
            @Override public boolean isEnabled(RecyclerView.ViewHolder holder) {
                int position = holder.getBindingAdapterPosition();
                return position >= 0 && position < TITLES.length && (position != 0 || IosGlassConfig.supported() || IosGlassConfig.enabled());
            }
        };
    }
}
