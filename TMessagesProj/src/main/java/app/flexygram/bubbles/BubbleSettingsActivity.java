package app.flexygram.bubbles;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.SeekBar;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Cells.TextCheckCell;
import tw.nekomimi.nekogram.ui.cells.HeaderCell;
import org.telegram.ui.Components.RecyclerListView;
import app.flexygram.settings.SignatureMatteSettingsActivity;

/** Local native preview, fill opacity, border width and optional cached wallpaper blur. */
public final class BubbleSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int SLIDER = 110, PREVIEW = 111;
    private boolean personalizationExpanded;
    private int personalizationRow;
    private app.flexygram.settings.signature.CompactStylePicker picker;
    private int effectRow, timestampRow;
    private int appearanceHeaderRow, borderHeaderRow, fusionHeaderRow;
    private int transparencyRow, borderRow, previewRow, positionRow, blurRow, enabledRow, fuseRow, styleRow, pearlRow, fusionIntensityRow, fusionAdaptRow;
    private BubblePreviewView preview;
    private final android.graphics.drawable.Drawable contextualWallpaper;
    public BubbleSettingsActivity() { this(null); }
    public BubbleSettingsActivity(android.graphics.drawable.Drawable contextualWallpaper) { this.contextualWallpaper = contextualWallpaper; }
    @Override protected void updateRows() {
        super.updateRows(); BubbleConfig.load();
        previewRow = addRow();
        personalizationRow = addRow("flexyBubblePersonalization");
        appearanceHeaderRow = borderHeaderRow = fusionHeaderRow = -1;
        effectRow = timestampRow = transparencyRow = blurRow = enabledRow = -1;
        borderRow = positionRow = fuseRow = styleRow = pearlRow = fusionIntensityRow = fusionAdaptRow = -1;
        if (!personalizationExpanded) return;
        appearanceHeaderRow = addHeader("FlexyBubbleAppearanceSection");
        effectRow = addRow("flexyBubbleSurfaceEffect");
        timestampRow = addRow("flexyBubbleSmallTimestamp");
        transparencyRow = blurRow = borderHeaderRow = enabledRow = fusionHeaderRow = -1;
        borderRow = positionRow = fuseRow = styleRow = pearlRow = fusionIntensityRow = fusionAdaptRow = -1;
        transparencyRow = addRow("flexyBubbleTransparency");
        blurRow = addRow("flexyBubbleBlur");
        borderHeaderRow = addHeader("FlexyBubbleBorderSection");
        enabledRow = addRow("flexyBubbleOutlineEnabled");
        fusionHeaderRow = -1;
        borderRow = positionRow = fuseRow = styleRow = pearlRow = fusionIntensityRow = fusionAdaptRow = -1;
        if (BubbleConfig.outlineEnabled()) {
            styleRow = addRow("flexyBubbleOutlineStyle"); borderRow = addRow("flexyBubbleBorderWidth");
            positionRow = addRow("flexyBubbleBorderPosition");
            if (BubbleConfig.outlineStyle() != 0) {
                pearlRow = addRow("flexyBubblePearlIntensity");
            }
            fusionHeaderRow = addHeader("FlexyBubbleFusionSection");
            fuseRow=addRow("flexyBubbleFusionMode");
            if(BubbleConfig.fusionMode()==2){fusionIntensityRow=addRow("flexyBubbleFusionIntensity");fusionAdaptRow=addRow("flexyBubbleFusionAdapt");}
        }
    }
    @Override protected String getActionBarTitle() { return getString(R.string.FlexyBubblesTitle); }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override public View createView(Context context) {
        View view = super.createView(context);
        listView.setItemAnimator(null);
        return view;
    }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position < 0) return;
        if (position == personalizationRow) {
            personalizationExpanded = !personalizationExpanded;
            updateRows(); listAdapter.notifyDataSetChanged();
        } else if (position == effectRow) {
            showDialog(new AlertDialog.Builder(getParentActivity(), resourcesProvider)
                    .setTitle(getString(R.string.FlexyBubbleSurfaceEffect))
                    .setItems(new CharSequence[]{getString(R.string.Default), getString(R.string.FlexyBubbleAdaptiveSurface), getString(R.string.FlexyBubbleLegacySurface)}, (dialog, which) -> {
                        BubbleConfig.setSurfaceEffect(new int[]{BubbleConfig.DEFAULT, BubbleConfig.ADAPTIVE, BubbleConfig.LEGACY}[which]);
                        updateRows(); listAdapter.notifyDataSetChanged();
                        settingsChanged();
                    }).create());
        } else if (position == timestampRow) {
            BubbleConfig.setSmallTimestamps(!BubbleConfig.smallTimestamps());
            listAdapter.notifyItemChanged(position);
            settingsChanged();
        } else if (position == enabledRow) {
            BubbleConfig.setOutlineEnabled(!BubbleConfig.outlineEnabled());
            updateRows(); listAdapter.notifyDataSetChanged(); settingsChanged();
        } else if (position == fuseRow) {
            showDialog(new AlertDialog.Builder(getParentActivity(),resourcesProvider).setTitle(getString(R.string.FlexyBubbleFusionMode)).setItems(new CharSequence[]{getString(R.string.FlexyBubbleFusionNone),getString(R.string.FlexyBubbleFusionClassic),"Flexy Bubble Fusion 2.0"},(dialog,which)->{BubbleConfig.setFusionMode(which);updateRows();listAdapter.notifyDataSetChanged();settingsChanged();}).create());
        } else if(position==fusionAdaptRow){
            BubbleConfig.setFusionAdapt(!BubbleConfig.fusionAdapt());listAdapter.notifyItemChanged(position);settingsChanged();
        } else if (position == styleRow) {
            showDialog(new AlertDialog.Builder(getParentActivity(), resourcesProvider).setTitle(getString(R.string.FlexyBubbleOutlineStyle))
                .setItems(new CharSequence[]{getString(R.string.FlexyBubbleOriginal),getString(R.string.FlexyBubbleGlassOriginal),getString(R.string.FlexyBubbleGlassPearl),getString(R.string.FlexyBubbleGlassSatin)},(dialog,which)->{
                    BubbleConfig.setOutlineStyle(new int[]{0, 3, 1, 2}[which]); updateRows(); listAdapter.notifyDataSetChanged();
                    settingsChanged();
                }).create());
        } else if (position == blurRow) {
            BubbleConfig.setBackgroundBlur(!BubbleConfig.backgroundBlur());
            updateRows(); listAdapter.notifyDataSetChanged();
            settingsChanged();
        }
    }
    @Override public void saveSelfArgs(Bundle args) { super.saveSelfArgs(args);args.putBoolean("bubblePersonalizationExpanded",personalizationExpanded); }
    @Override public void restoreSelfArgs(Bundle args) { super.restoreSelfArgs(args);personalizationExpanded=args.getBoolean("bubblePersonalizationExpanded",false); }
    @Override public void scrollToRow(String key, Runnable unknown) {
        if (key != null && key.startsWith("flexyBubble") && !personalizationExpanded) {
            personalizationExpanded=true;updateRows();if(listAdapter!=null)listAdapter.notifyDataSetChanged();
        }
        super.scrollToRow(key,unknown);
    }
    private View createGallery(Context context) {
        preview = new BubblePreviewView(context,contextualWallpaper);
        picker = new app.flexygram.settings.signature.CompactStylePicker(context,resourcesProvider,preview,3);
        int[] styles={BubbleConfig.TELEGRAM,BubbleConfig.FLEXYGRAM,BubbleConfig.IPHONE};
        int[] names={R.string.FlexyBubbleShapeTelegram,R.string.FlexyBubbleShapeFlexyGram,R.string.FlexyBubbleShapeIPhone};
        for(int i=0;i<styles.length;i++) {
            final int shape=styles[i];
            picker.addChoice(shape,getString(names[i]),new BubbleShapeMiniature(context,shape),()->{
                BubbleConfig.setShape(shape);picker.select(shape);picker.refreshMiniatures();preview.settingsChanged();
            });
        }
        picker.select(BubbleConfig.shape());
        picker.setLayoutParams(new RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));
        return picker;
    }
    private void settingsChanged() {
        if(preview!=null)preview.settingsChanged();
        if(picker!=null)picker.refreshMiniatures();
    }
    private String[] borderPositions() {
        return new String[]{getString(R.string.FlexyBubbleBorderTop),
                getString(R.string.FlexyBubbleBorderBottom), getString(R.string.FlexyBubbleBorderLeft),
                getString(R.string.FlexyBubbleBorderRight), getString(R.string.FlexyBubbleBorderFull)};
    }
    private final class TransparencyCell extends LinearLayout implements Theme.Colorable {
        @Override public void updateColors(){title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));seek.invalidate();}
        boolean border, pearl, position, fusion;
        final TextView title;
        final SeekBar seek;
        boolean binding;
        TransparencyCell(Context context) {
            super(context); setOrientation(VERTICAL); setPadding(dp(16), dp(6), dp(16), dp(2));
            title = new TextView(context); title.setTextSize(15);
            title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            addView(title, new LinearLayout.LayoutParams(-1, -2));
            seek = new app.flexygram.settings.FlexySignatureSlider(context); seek.setMax(100);
            addView(seek, new LinearLayout.LayoutParams(-1, dp(48)));
            seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onStartTrackingTouch(SeekBar bar) { bar.getParent().requestDisallowInterceptTouchEvent(true); }
                public void onStopTrackingTouch(SeekBar bar) { bar.getParent().requestDisallowInterceptTouchEvent(false); }
                public void onProgressChanged(SeekBar bar, int value, boolean user) {
                    if (user && !binding) { if(fusion)BubbleConfig.setFusionIntensity(value);else if (position) BubbleConfig.setBorderPosition(value + 1); else if (border) BubbleConfig.setBorderTenths(value); else if (pearl) BubbleConfig.setPearlIntensity(value); else BubbleConfig.setTransparency(value); settingsChanged(); }
                    label(value);
                }
            });
        }
        void label(int value) {
            String text = fusion?getString(R.string.FlexyBubbleFusionIntensity)+" · "+value+" %":position ? getString(R.string.FlexyBubbleBorderPosition) + " · " + borderPositions()[value] : border ? getString(R.string.FlexyBubbleBorderWidth) + " · " + String.format(java.util.Locale.US, "%.1f dp", value/10f) : getString(pearl ? R.string.FlexyBubblePearlIntensity : R.string.FlexyBubblesTransparency) + " · " + value + " %";
            title.setText(text); seek.setContentDescription(text);
        }
        void bind(boolean border) { bind(border, false, false); }
        void bind(boolean border,boolean pearl,boolean position){bind(border,pearl,position,false);}
        void bind(boolean border, boolean pearl, boolean position,boolean fusion) {
            this.fusion=fusion;
            this.position = position;
            this.border = border; this.pearl = pearl;
            binding = true; seek.setMax(position ? 4 : border ? 20 : 100); int value = fusion?BubbleConfig.fusionIntensity():position ? BubbleConfig.borderPosition() - 1 : border ? BubbleConfig.borderTenths() : pearl ? BubbleConfig.pearlIntensity() : BubbleConfig.transparency(); seek.setProgress(value); label(value);
            seek.setEnabled(!pearl || BubbleConfig.outlineStyle() >= 1); setAlpha(!pearl || BubbleConfig.outlineStyle() >= 1 ? 1f : .5f); binding = false;
        }
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) {
            if (position == appearanceHeaderRow || position == borderHeaderRow || position == fusionHeaderRow) return TYPE_HEADER;
            return position == previewRow ? PREVIEW : position == timestampRow || position == blurRow || position == fusionAdaptRow || position == enabledRow ? TYPE_CHECK : position == personalizationRow || position == effectRow || position == styleRow || position == fuseRow ? TYPE_SETTINGS : position == transparencyRow || position == borderRow || position == pearlRow || position == positionRow || position == fusionIntensityRow ? SLIDER : TYPE_INFO_PRIVACY;
        }
        @Override protected boolean isSectionContent(int type) {
            // Wallpaper and section labels separate the three compact control groups.
            return type != PREVIEW && type != TYPE_HEADER && super.isSectionContent(type);
        }
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int type) {
            if (type == PREVIEW) {
                return new RecyclerListView.Holder(createGallery(parent.getContext()));
            }
            if (type == SLIDER) {
                TransparencyCell cell = new TransparencyCell(parent.getContext());
                cell.setLayoutParams(new RecyclerView.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
                return new RecyclerListView.Holder(cell);
            }
            RecyclerView.ViewHolder holder = super.onCreateViewHolder(parent, type);
            if (type == TYPE_HEADER) {
                // Section labels always stay on the page background, regardless of global header styling.
                HeaderCell header = (HeaderCell) holder.itemView;
                header.setTag(RecyclerListView.TAG_NOT_SECTION);
                header.setBackground(null);
                header.setPadding(dp(24), dp(6), dp(24), dp(3));
                header.setHeight(34);
            }
            return holder;
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            if (position == previewRow) {
                picker=(app.flexygram.settings.signature.CompactStylePicker)holder.itemView;
                preview=(BubblePreviewView)picker.previewView();
                picker.select(BubbleConfig.shape());picker.refreshMiniatures();holder.itemView.invalidate();return;
            }
            if(position==personalizationRow) {
                ((TextSettingsCell)holder.itemView).setTextAndValue(getString(R.string.FlexyBubblePersonalization),
                        getString(personalizationExpanded?R.string.FlexyBubblePersonalizationHide:R.string.FlexyBubblePersonalizationShow),false);
                return;
            }
            if (position == timestampRow) {
                ((TextCheckCell) holder.itemView).setTextAndCheck(getString(R.string.FlexyBubbleSmallTimestamp), BubbleConfig.smallTimestamps(), false);
                return;
            }
            if (position == effectRow) {
                ((TextSettingsCell) holder.itemView).setTextAndValue(getString(R.string.FlexyBubbleSurfaceEffect),
                        getString(BubbleConfig.surfaceEffect() == BubbleConfig.DEFAULT ? R.string.Default : BubbleConfig.adaptive() ? R.string.FlexyBubbleAdaptiveSurface : R.string.FlexyBubbleLegacySurface), false);
                return;
            }
            if (position == appearanceHeaderRow || position == borderHeaderRow || position == fusionHeaderRow) {
                ((HeaderCell) holder.itemView).setText(getString(position == appearanceHeaderRow
                        ? R.string.FlexyBubbleAppearanceSection : position == borderHeaderRow
                        ? R.string.FlexyBubbleBorderSection : R.string.FlexyBubbleFusionSection));
                return;
            }
            if (position == transparencyRow || position == borderRow || position == pearlRow || position == positionRow || position == fusionIntensityRow) { ((TransparencyCell)holder.itemView).bind(position == borderRow, position == pearlRow, position == positionRow,position==fusionIntensityRow); return; }
            if (position == enabledRow) { ((TextCheckCell)holder.itemView).setTextAndCheck(getString(R.string.FlexyBubbleOutlineEnabled), BubbleConfig.outlineEnabled(), false); return; }
            if (position == fuseRow) {
                ((TextSettingsCell)holder.itemView).setTextAndValue(getString(R.string.FlexyBubbleFusionMode),BubbleConfig.fusionMode()==2?"Flexy Bubble Fusion 2.0":getString(BubbleConfig.fusionMode()==1?R.string.FlexyBubbleFusionClassic:R.string.FlexyBubbleFusionNone),true);return;
            }
            if(position==fusionAdaptRow){((TextCheckCell)holder.itemView).setTextAndCheck(getString(R.string.FlexyBubbleFusionAdapt),BubbleConfig.fusionAdapt(),true);return;}
            if (position == styleRow) {
                ((TextSettingsCell)holder.itemView).setTextAndValue(getString(R.string.FlexyBubbleOutlineStyle),
                        getString(BubbleConfig.outlineStyle() == 0 ? R.string.FlexyBubbleOriginal : BubbleConfig.outlineStyle() == 3 ? R.string.FlexyBubbleGlassOriginal : BubbleConfig.outlineStyle() == 2 ? R.string.FlexyBubbleGlassSatin : R.string.FlexyBubbleGlassPearl), true); return;
            }
            if (position == blurRow) { ((TextCheckCell)holder.itemView).setTextAndCheck(getString(R.string.FlexyBubbleBackgroundBlur), BubbleConfig.backgroundBlur(), false); return; }


        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) { int p = settingsRowPosition(holder); if (p < 0) return false; return p == personalizationRow || p == timestampRow || p == effectRow || p == blurRow || p == styleRow || p == fuseRow || p == enabledRow || p==fusionAdaptRow; }
    }
}
