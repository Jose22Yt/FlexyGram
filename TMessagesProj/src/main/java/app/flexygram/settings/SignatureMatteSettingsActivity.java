package app.flexygram.settings;

import android.content.Context;
import android.util.TypedValue;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import app.exteraless.appearance.SectionCardRecyclerView;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.RecyclerListView;
import tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity;

/** Shared grouped settings surfaces. No preference writes or changes to global Glass. */
public abstract class SignatureMatteSettingsActivity extends BaseNekoSettingsActivity {
    @Override public org.telegram.ui.ActionBar.ActionBar createActionBar(Context context){org.telegram.ui.ActionBar.ActionBar bar=super.createActionBar(context);bar.centerTitle();return bar;}
    protected int matteHeaderColor() { return getThemedColor(Theme.key_windowBackgroundWhiteBlueHeader); }
    @Override protected boolean usesSolidSettingsSurfaces() { return true; }
    @Override protected boolean needActionBarBlur() { return false; }
    @Override protected void setupAdaptiveBackground() {
        actionBar.setDrawGlassTitle(false);
        actionBar.doNotDrawGlassMenu = true;
    }

    @Override
    protected SectionCardRecyclerView createSettingsList(Context context) {
        return new MatteSectionList(context);
    }

    protected int addHeader(String key) {
        return addRow(key);
    }

    protected abstract class MatteListAdapter extends BaseListAdapter {
        protected MatteListAdapter(Context context) { super(context); }

        @NonNull @Override
        public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int type) {
            View view;
            if (type == TYPE_SETTINGS) {
                view = new MatteTextSettingsCell(mContext, resourcesProvider);
            } else if (type == TYPE_CHECK) {
                view = new MatteTextCheckCell(mContext, resourcesProvider);
            } else if (type == TYPE_DETAIL_SETTINGS) {
                view = new MatteDetailSettingsCell(mContext);
            } else {
                return super.onCreateViewHolder(parent, type);
            }
            view.setLayoutParams(new RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            return new RecyclerListView.Holder(view);
        }

        @Override
        protected boolean isSectionContent(int type) {
            // Preserve previews/sliders as part of the native card, without extra backdrops.
            return type >= 100 || super.isSectionContent(type);
        }

        @Override
        public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position) {
            super.onBindViewHolder(holder, position);
            if (holder.itemView instanceof tw.nekomimi.nekogram.ui.cells.HeaderCell) {
                tw.nekomimi.nekogram.ui.cells.HeaderCell header = (tw.nekomimi.nekogram.ui.cells.HeaderCell) holder.itemView;
                header.setTextColor(matteHeaderColor());
                if (header.getTextView() != null) {
                    header.getTextView().setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
                    header.getTextView().setSingleLine(false);
                    header.getTextView().setMaxLines(Integer.MAX_VALUE);
                }
            }
            if (holder.itemView instanceof org.telegram.ui.Cells.CheckBoxCell) {
                org.telegram.ui.Cells.CheckBoxCell cell = (org.telegram.ui.Cells.CheckBoxCell) holder.itemView;
                cell.setMultiline(true);
                if (cell.getTextView() != null) cell.getTextView().setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
            }

        }
    }

    private final class MatteSectionList extends SectionCardRecyclerView {
        MatteSectionList(Context context) { super(context); setCardResourcesProvider(SignatureMatteSettingsActivity.this.resourcesProvider); }
        @Override protected int measureBlurTopPadding() { return 0; }

    }
}
