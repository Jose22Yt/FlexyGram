package app.flexygram.bubbles;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.SeekBar;
import android.graphics.drawable.GradientDrawable;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Components.RecyclerListView;
import app.flexygram.settings.SignatureMatteSettingsActivity;

/** Local native preview, fill opacity, border width and optional cached wallpaper blur. */
public final class BubbleSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int SLIDER = 110;
    private int transparencyRow, borderRow, previewRow, positionRow, blurRow, enabledRow, fuseRow, styleRow, pearlRow, glassStrengthRow, surfaceRow, outgoingRow, incomingRow;
    private BubblePreviewView preview;
    private final android.graphics.drawable.Drawable contextualWallpaper;
    public BubbleSettingsActivity() { this(null); }
    public BubbleSettingsActivity(android.graphics.drawable.Drawable contextualWallpaper) { this.contextualWallpaper = contextualWallpaper; }
    @Override protected void updateRows() {
        super.updateRows(); BubbleConfig.load();
        previewRow = addRow(); surfaceRow = addRow("flexyBubbleSurface"); transparencyRow = addRow("flexyBubbleTransparency");
        blurRow = addRow("flexyBubbleGlassEnabled");
        glassStrengthRow = BubbleConfig.bubbleGlassEnabled() ? addRow("flexyBubbleGlassStrength") : -1;
        outgoingRow = BubbleConfig.bubbleGlassEnabled() ? addRow("flexyBubbleGlassOutgoing") : -1;
        incomingRow = BubbleConfig.bubbleGlassEnabled() ? addRow("flexyBubbleGlassIncoming") : -1;
        enabledRow = addRow("flexyBubbleOutlineEnabled");
        borderRow = positionRow = fuseRow = styleRow = pearlRow = -1;
        if (BubbleConfig.outlineEnabled()) {
            styleRow = addRow("flexyBubbleOutlineStyle"); borderRow = addRow("flexyBubbleBorderWidth");
            positionRow = addRow("flexyBubbleBorderPosition");
            if (BubbleConfig.outlineStyle() != 0) {
                pearlRow = addRow("flexyBubblePearlIntensity"); fuseRow = addRow("flexyBubbleFuseGlass");
            }
        }
    }
    @Override protected String getActionBarTitle() { return getString(R.string.FlexyBubblesTitle); }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position < 0) return;
        if (position == surfaceRow) {
            showDialog(new AlertDialog.Builder(getParentActivity(), resourcesProvider)
                .setTitle(getString(R.string.FlexyBubbleSurface))
                .setItems(new CharSequence[]{getString(R.string.FlexyBubbleSurfaceClassic), "Glass"}, (dialog, which) -> {
                    BubbleConfig.setBubbleGlassEnabled(which == 1);
                    updateRows(); listAdapter.notifyDataSetChanged();
                    if (preview != null) preview.settingsChanged();
                }).create());
        } else if (position == outgoingRow || position == incomingRow) {
            if (position == outgoingRow) BubbleConfig.setGlassOutgoing(!BubbleConfig.glassOutgoing());
            else BubbleConfig.setGlassIncoming(!BubbleConfig.glassIncoming());
            listAdapter.notifyItemChanged(position);
            if (preview != null) preview.settingsChanged();
        } else if (position == enabledRow) {
            BubbleConfig.setOutlineEnabled(!BubbleConfig.outlineEnabled());
            updateRows(); listAdapter.notifyDataSetChanged(); if (preview != null) preview.settingsChanged();
        } else if (position == fuseRow) {
            BubbleConfig.setFuseGlass(!BubbleConfig.fuseGlass());
            listAdapter.notifyItemChanged(position); if (preview != null) preview.settingsChanged();
        } else if (position == styleRow) {
            showDialog(new AlertDialog.Builder(getParentActivity(), resourcesProvider).setTitle(getString(R.string.FlexyBubbleOutlineStyle))
                .setItems(new CharSequence[]{getString(R.string.FlexyBubbleOriginal),getString(R.string.FlexyBubbleGlassOriginal),getString(R.string.FlexyBubbleGlassPearl),getString(R.string.FlexyBubbleGlassSatin)},(dialog,which)->{
                    BubbleConfig.setOutlineStyle(new int[]{0, 3, 1, 2}[which]); updateRows(); listAdapter.notifyDataSetChanged();
                    if (preview != null) preview.settingsChanged();
                }).create());
        } else if (position == blurRow) {
            BubbleConfig.setBubbleGlassEnabled(!BubbleConfig.bubbleGlassEnabled());
            updateRows(); listAdapter.notifyDataSetChanged();
            if (preview != null) preview.settingsChanged();
        }
    }
    private String[] borderPositions() {
        return new String[]{getString(R.string.FlexyBubbleBorderTop),
                getString(R.string.FlexyBubbleBorderBottom), getString(R.string.FlexyBubbleBorderLeft),
                getString(R.string.FlexyBubbleBorderRight), getString(R.string.FlexyBubbleBorderFull)};
    }
    private final class TransparencyCell extends LinearLayout implements Theme.Colorable {
        @Override public void updateColors(){title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));seek.invalidate();}
        boolean border, pearl, position, glassIntensity;
        final TextView title;
        final SeekBar seek;
        boolean binding;
        TransparencyCell(Context context) {
            super(context); setOrientation(VERTICAL); setPadding(dp(20), dp(12), dp(20), dp(4));
            title = new TextView(context); title.setTextSize(16);
            title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            addView(title, new LinearLayout.LayoutParams(-1, -2));
            seek = new app.flexygram.settings.FlexySignatureSlider(context); seek.setMax(100);
            addView(seek, new LinearLayout.LayoutParams(-1, dp(48)));
            seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onStartTrackingTouch(SeekBar bar) { bar.getParent().requestDisallowInterceptTouchEvent(true); }
                public void onStopTrackingTouch(SeekBar bar) { bar.getParent().requestDisallowInterceptTouchEvent(false); }
                public void onProgressChanged(SeekBar bar, int value, boolean user) {
                    if (user && !binding) { if (position) BubbleConfig.setBorderPosition(value + 1); else if (border) BubbleConfig.setBorderTenths(value+5); else if (pearl) BubbleConfig.setPearlIntensity(value); else if (glassIntensity) BubbleConfig.setGlassIntensity(value); else BubbleConfig.setTransparency(value); if (preview != null) preview.settingsChanged(); }
                    label(value);
                }
            });
        }
        void label(int value) {
            String text = position ? getString(R.string.FlexyBubbleBorderPosition) + " · " + borderPositions()[value] : border ? getString(R.string.FlexyBubbleBorderWidth) + " · " + String.format(java.util.Locale.US, "%.1f dp", (value+5)/10f) : getString(glassIntensity ? R.string.FlexyBubbleGlassStrength : pearl ? R.string.FlexyBubblePearlIntensity : R.string.FlexyBubblesTransparency) + " · " + value + " %";
            title.setText(text); seek.setContentDescription(text);
        }
        void bind(boolean border) { bind(border, false, false, false); }
        void bind(boolean border, boolean pearl, boolean position, boolean glassIntensity) {
            this.position = position;
            this.border = border; this.pearl = pearl; this.glassIntensity = glassIntensity;
            binding = true; seek.setMax(position ? 4 : border ? 15 : 100); int value = position ? BubbleConfig.borderPosition() - 1 : border ? BubbleConfig.borderTenths()-5 : pearl ? BubbleConfig.pearlIntensity() : glassIntensity ? BubbleConfig.glassIntensity() : BubbleConfig.transparency(); seek.setProgress(value); label(value);
            seek.setEnabled(!pearl || BubbleConfig.outlineStyle() >= 1); setAlpha(!pearl || BubbleConfig.outlineStyle() >= 1 ? 1f : .5f); binding = false;
        }
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) {
            return position == previewRow ? 111 : position == blurRow || position == outgoingRow || position == incomingRow || position == fuseRow || position == enabledRow ? TYPE_CHECK : position == styleRow || position == surfaceRow ? TYPE_SETTINGS : position == transparencyRow || position == borderRow || position == pearlRow || position == positionRow || position == glassStrengthRow ? SLIDER : TYPE_INFO_PRIVACY;
        }
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int type) {
            if (type == 111) { preview = new BubblePreviewView(parent.getContext(), contextualWallpaper); return new RecyclerListView.Holder(preview); }
            if (type == SLIDER) return new RecyclerListView.Holder(new TransparencyCell(parent.getContext()));
            return super.onCreateViewHolder(parent, type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            if (position == previewRow) { holder.itemView.invalidate(); return; }
            if (position == transparencyRow || position == borderRow || position == pearlRow || position == positionRow || position == glassStrengthRow) { ((TransparencyCell)holder.itemView).bind(position == borderRow, position == pearlRow, position == positionRow, position == glassStrengthRow); return; }
            if (position == surfaceRow) { ((TextSettingsCell)holder.itemView).setTextAndValue(getString(R.string.FlexyBubbleSurface), BubbleConfig.bubbleGlassEnabled() ? "Glass" : getString(R.string.FlexyBubbleSurfaceClassic), true); return; }
            if (position == outgoingRow || position == incomingRow) {
                ((TextCheckCell)holder.itemView).setTextAndCheck(getString(position == outgoingRow ? R.string.FlexyBubbleGlassOutgoing : R.string.FlexyBubbleGlassIncoming), position == outgoingRow ? BubbleConfig.glassOutgoing() : BubbleConfig.glassIncoming(), true); return;
            }
            if (position == enabledRow) { ((TextCheckCell)holder.itemView).setTextAndCheck(getString(R.string.FlexyBubbleOutlineEnabled), BubbleConfig.outlineEnabled(), false); return; }
            if (position == fuseRow) {
                ((TextCheckCell)holder.itemView).setTextAndCheck(getString(R.string.FlexyBubbleFuseGlass), BubbleConfig.fuseGlass(), false); return;
            }
            if (position == styleRow) {
                ((TextSettingsCell)holder.itemView).setTextAndValue(getString(R.string.FlexyBubbleOutlineStyle),
                        getString(BubbleConfig.outlineStyle() == 0 ? R.string.FlexyBubbleOriginal : BubbleConfig.outlineStyle() == 3 ? R.string.FlexyBubbleGlassOriginal : BubbleConfig.outlineStyle() == 2 ? R.string.FlexyBubbleGlassSatin : R.string.FlexyBubbleGlassPearl), true); return;
            }
            if (position == blurRow) { ((TextCheckCell)holder.itemView).setTextAndCheck(getString(R.string.FlexyBubbleGlassEnabled), BubbleConfig.bubbleGlassEnabled(), false); return; }


        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) { int p = holder.getAdapterPosition(); if (p < 0) return false; return p == blurRow || p == surfaceRow || p == outgoingRow || p == incomingRow || p == styleRow || p == fuseRow || p == enabledRow; }
    }
}
