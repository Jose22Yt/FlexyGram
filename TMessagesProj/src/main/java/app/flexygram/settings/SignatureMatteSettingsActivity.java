package app.flexygram.settings;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
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

/** Opt-in for General/Appearance only. No preference writes or changes to global Glass. */
public abstract class SignatureMatteSettingsActivity extends BaseNekoSettingsActivity {
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
                header.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteGrayText2));
                header.getTextView().setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
                header.getTextView().setSingleLine(false);
                header.getTextView().setMaxLines(Integer.MAX_VALUE);
            }
            if (holder.itemView instanceof org.telegram.ui.Cells.CheckBoxCell) {
                org.telegram.ui.Cells.CheckBoxCell cell = (org.telegram.ui.Cells.CheckBoxCell) holder.itemView;
                cell.setMultiline(true);
                if (cell.getTextView() != null) cell.getTextView().setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
            }

        }
    }

    private final class MatteSectionList extends SectionCardRecyclerView {
        private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path shape = new Path();
        private final float[] corners = new float[8];

        MatteSectionList(Context context) { super(context); }
        @Override protected int measureBlurTopPadding() { return 0; }

        @Override
        public void drawBackgroundRect(Canvas canvas, RectF rect, float topRadius, float bottomRadius, float alpha) {
            // Opaque native theme surface, including dark/carbon themes. No shadow/blur layer.
            fill.setColor(Theme.getColor(Theme.key_windowBackgroundWhite, SignatureMatteSettingsActivity.this.resourcesProvider) | 0xFF000000);
            if (topRadius == bottomRadius) {
                canvas.drawRoundRect(rect, topRadius, topRadius, fill);
            } else {
                shape.rewind();
                corners[0] = corners[1] = corners[2] = corners[3] = topRadius;
                corners[4] = corners[5] = corners[6] = corners[7] = bottomRadius;
                shape.addRoundRect(rect, corners, Path.Direction.CW);
                canvas.drawPath(shape, fill);
            }
        }
    }
}
