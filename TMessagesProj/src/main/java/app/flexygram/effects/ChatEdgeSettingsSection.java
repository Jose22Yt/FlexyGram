package app.flexygram.effects;

import android.content.Context;
import android.view.View;

import androidx.recyclerview.widget.RecyclerView;

import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.AlertsCreator;

public final class ChatEdgeSettingsSection extends SignatureMatteSettingsActivity {
    private int styleRow;

    @Override
    protected String getActionBarTitle() {
        return LocaleController.getString(R.string.FlexyChatEdgeStyle);
    }

    @Override
    protected void updateRows() {
        super.updateRows();
        styleRow = addRow("flexyChatEdgeReflection");
    }

    @Override
    public int getSearchGuid() {
        return 11_100_000;
    }

    @Override
    public int getSearchIcon() {
        return R.drawable.fg_dm_bordes_reflejos;
    }

    @Override
    public String getSearchPrefix() {
        return "Flexy";
    }

    @Override
    protected void onItemClick(View view, int position, float x, float y) {
        if (position != styleRow || getParentActivity() == null) return;
        final String[] choices = {
                LocaleController.getString(R.string.FlexyChatEdgeCurrent),
                LocaleController.getString(R.string.FlexyChatEdgeReflection)
        };
        showDialog(AlertsCreator.createSingleChoiceDialog(getParentActivity(), choices, getActionBarTitle(),
                ChatEdgeStyle.isReflective() ? 1 : 0, (dialog, which) -> {
                    ChatEdgeStyle.setReflective(which == 1);
                    if (listAdapter != null) listAdapter.notifyItemChanged(styleRow);
                }));
    }

    @Override
    protected BaseListAdapter createAdapter(Context context) {
        return new MatteListAdapter(context) {
            @Override
            public int getItemViewType(int position) {
                return TYPE_SETTINGS;
            }

            @Override
            public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
                ((TextSettingsCell) holder.itemView).setTextAndValue(getActionBarTitle(),
                        LocaleController.getString(ChatEdgeStyle.isReflective()
                                ? R.string.FlexyChatEdgeReflection : R.string.FlexyChatEdgeCurrent), false);
            }

            @Override
            public boolean isEnabled(RecyclerView.ViewHolder holder) {
                return true;
            }
        };
    }
}
