package app.flexygram.header;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.HeaderCell;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.RecyclerListView;

public final class HeaderSettingsActivity extends SignatureMatteSettingsActivity {
    private int previewRow;
    private int cherryHeaderRow, centerTitleRow, adaptiveBubbleRow, counterRow, iosStyledCounterRow;
    private int geometryHeaderRow, styleRow, sizeRow, opacityRow;
    private HeaderPreviewView preview;

    @Override
    protected void updateRows() {
        super.updateRows();
        HeaderConfig.load();
        previewRow = addRow();

        cherryHeaderRow = addRow("FlexyHeaderCherrySection");
        centerTitleRow = addRow("signatureHeaderCenterTitle");
        adaptiveBubbleRow = addRow("signatureHeaderAdaptiveBubble");
        counterRow = addRow("signatureHeaderCounter");
        iosStyledCounterRow = HeaderConfig.counter() ? addRow("signatureHeaderIosCounter") : -1;

        geometryHeaderRow = addRow("FlexyHeaderGeometrySection");
        styleRow = addRow("signatureHeaderStyle");
        sizeRow = HeaderConfig.portrait() ? -1 : addRow("signatureHeaderSize");
        opacityRow = HeaderConfig.portrait() ? -1 : addRow("signatureHeaderOpacity");
    }

    @Override
    protected String getActionBarTitle() {
        return getString(R.string.FlexyHeaderTitle);
    }

    @Override
    protected BaseListAdapter createAdapter(Context c) {
        return new Adapter(c);
    }

    private void changed(int row) {
        if (row == styleRow || row == counterRow) {
            updateRows();
            listAdapter.notifyDataSetChanged();
        } else {
            listAdapter.notifyItemChanged(row);
        }
        if (preview != null) {
            preview.settingsChanged();
        }
    }

    @Override
    protected void onItemClick(View v, int position, float x, float y) {
        if (position == centerTitleRow) {
            HeaderConfig.centerTitle(!HeaderConfig.centerTitle());
            changed(centerTitleRow);
        } else if (position == adaptiveBubbleRow) {
            HeaderConfig.adaptiveBubble(!HeaderConfig.adaptiveBubble());
            changed(adaptiveBubbleRow);
        } else if (position == counterRow) {
            HeaderConfig.counter(!HeaderConfig.counter());
            changed(counterRow);
        } else if (position == iosStyledCounterRow) {
            HeaderConfig.counterMode(HeaderConfig.counterMode() == 1 ? 2 : 1);
            changed(iosStyledCounterRow);
        } else if (position == styleRow || position == sizeRow) {
            boolean style = position == styleRow;
            showDialog(new AlertDialog.Builder(getParentActivity(), resourcesProvider)
                    .setTitle(getString(style ? R.string.FlexyHeaderStyle : R.string.FlexyHeaderSize))
                    .setItems(style ? new CharSequence[]{
                            getString(R.string.FlexyHeaderPortrait),
                            getString(R.string.FlexyHeaderSignature),
                            getString(R.string.FlexyHeaderFusion),
                            getString(R.string.FlexyHeaderClassic)
                    } : new CharSequence[]{
                            getString(R.string.FlexyHeaderNormal),
                            getString(R.string.FlexyHeaderCompact)
                    }, (dialog, which) -> {
                        if (style) HeaderConfig.style(new int[]{3, 0, 2, 1}[which]);
                        else HeaderConfig.compact(which == 1);
                        changed(position);
                    }).create());
        }
    }

    private final class OpacityCell extends LinearLayout implements Theme.Colorable {
        @Override
        public void updateColors() {
            label.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            slider.invalidate();
        }
        final TextView label;
        final SeekBar slider;
        boolean binding;

        OpacityCell(Context c) {
            super(c);
            setOrientation(VERTICAL);
            setPadding(dp(20), dp(12), dp(20), dp(4));
            label = new TextView(c);
            label.setTextSize(16);
            label.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            addView(label, new LayoutParams(-1, -2));
            slider = new app.flexygram.settings.FlexySignatureSlider(c);
            slider.setMax(100);
            addView(slider, new LayoutParams(-1, dp(48)));
            slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onStartTrackingTouch(SeekBar b) { b.getParent().requestDisallowInterceptTouchEvent(true); }
                public void onStopTrackingTouch(SeekBar b) { b.getParent().requestDisallowInterceptTouchEvent(false); }
                public void onProgressChanged(SeekBar b, int value, boolean user) {
                    if (user && !binding) {
                        HeaderConfig.opacity(value);
                        if (preview != null) preview.invalidate();
                    }
                    label(value);
                }
            });
        }

        void label(int value) {
            String title = getString(R.string.FlexyHeaderOpacity) + " · " + value + " %";
            label.setText(title);
            slider.setContentDescription(title);
        }

        void bind() {
            binding = true;
            slider.setProgress(HeaderConfig.opacity());
            label(HeaderConfig.opacity());
            binding = false;
        }
    }

    private final class Adapter extends MatteListAdapter {
        Adapter(Context c) { super(c); }

        @Override
        public int getItemViewType(int p) {
            if (p == previewRow) return 111;
            if (p == opacityRow) return 112;
            if (p == cherryHeaderRow || p == geometryHeaderRow) return TYPE_HEADER;
            if (p == centerTitleRow || p == adaptiveBubbleRow || p == counterRow || p == iosStyledCounterRow) return TYPE_CHECK;
            return TYPE_SETTINGS;
        }

        @Override
        public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup p, int type) {
            if (type == 111) {
                preview = new HeaderPreviewView(p.getContext());
                return new RecyclerListView.Holder(preview);
            }
            if (type == 112) {
                return new RecyclerListView.Holder(new OpacityCell(p.getContext()));
            }
            return super.onCreateViewHolder(p, type);
        }

        @Override
        public void onBindViewHolder(RecyclerView.ViewHolder h, int p, boolean partial) {
            if (p == previewRow) {
                h.itemView.invalidate();
                return;
            }
            if (p == opacityRow) {
                ((OpacityCell) h.itemView).bind();
                return;
            }
            if (p == cherryHeaderRow) {
                ((HeaderCell) h.itemView).setText(getString(R.string.FlexyHeaderCherrySection));
                return;
            }
            if (p == geometryHeaderRow) {
                ((HeaderCell) h.itemView).setText(getString(R.string.FlexyHeaderGeometrySection));
                return;
            }
            if (p == centerTitleRow) {
                ((TextCheckCell) h.itemView).setTextAndCheck(getString(R.string.FlexyHeaderCenterTitle), HeaderConfig.centerTitle(), true);
                return;
            }
            if (p == adaptiveBubbleRow) {
                ((TextCheckCell) h.itemView).setTextAndCheck(getString(R.string.FlexyHeaderAdaptiveBubble), HeaderConfig.adaptiveBubble(), true);
                return;
            }
            if (p == counterRow) {
                ((TextCheckCell) h.itemView).setTextAndValueAndCheck(getString(R.string.FlexyHeaderShowUnread), getString(R.string.FlexyHeaderShowUnreadSub), HeaderConfig.counter(), false, iosStyledCounterRow != -1);
                return;
            }
            if (p == iosStyledCounterRow) {
                ((TextCheckCell) h.itemView).setTextAndCheck(getString(R.string.FlexyHeaderIosStyledCounter), HeaderConfig.counterMode() == 1, false);
                return;
            }
            ((TextSettingsCell) h.itemView).setTextAndValue(
                    getString(p == styleRow ? R.string.FlexyHeaderStyle : R.string.FlexyHeaderSize),
                    getString(p == styleRow
                            ? (HeaderConfig.portrait() ? R.string.FlexyHeaderPortrait : HeaderConfig.fusion() ? R.string.FlexyHeaderFusion : HeaderConfig.signature() ? R.string.FlexyHeaderSignature : R.string.FlexyHeaderClassic)
                            : (HeaderConfig.compact() ? R.string.FlexyHeaderCompact : R.string.FlexyHeaderNormal)),
                    p != sizeRow || opacityRow != -1
            );
        }

        @Override
        public boolean isEnabled(RecyclerView.ViewHolder h) {
            int p = h.getAdapterPosition();
            return p != previewRow && p != opacityRow && p != cherryHeaderRow && p != geometryHeaderRow;
        }
    }
}
