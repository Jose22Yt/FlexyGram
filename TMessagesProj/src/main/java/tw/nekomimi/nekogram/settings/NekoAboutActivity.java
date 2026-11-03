package tw.nekomimi.nekogram.settings;

import static org.telegram.messenger.LocaleController.getString;

import android.content.Context;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import org.telegram.messenger.BuildVars;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.messenger.R;
import org.telegram.messenger.browser.Browser;
import org.telegram.ui.Cells.TextSettingsCell;

import tw.nekomimi.nekogram.DatacenterActivity;

public class NekoAboutActivity extends BaseNekoSettingsActivity {

    private int aboutRow;
    private int sourceCodeRow;
    private int licenseRow;
    private int datacenterStatusRow;

    @Override
    protected void updateRows() {
        super.updateRows();
        aboutRow = addRow();
        sourceCodeRow = addRow();
        licenseRow = addRow();
        datacenterStatusRow = addRow();
    }

    @Override
    protected String getActionBarTitle() {
        return getString(R.string.FlexySettingsAbout);
    }

    @Override
    protected void onItemClick(View view, int position, float x, float y) {
        if (position == aboutRow) {
            showDialog(new AlertDialog.Builder(getParentActivity(), resourcesProvider)
                    .setTitle(getString(R.string.FlexySettingsAbout))
                    .setMessage(getString(R.string.FlexySettingsAboutBody) + "\n\n" + getString(R.string.FlexySettingsCreditsBody))
                    .setPositiveButton(getString(R.string.OK), null).create());
        } else if (position == sourceCodeRow) {
            Browser.openUrl(getParentActivity(), "https://github.com/Jose22Yt/FlexyGram");
        } else if (position == licenseRow) {
            Browser.openUrl(getParentActivity(), "https://github.com/Jose22Yt/FlexyGram/blob/main/LICENSE");
        } else if (position == datacenterStatusRow) {
            presentFragment(new DatacenterActivity(0));
        }
    }

    @Override
    protected BaseListAdapter createAdapter(Context context) {
        return new ListAdapter(context);
    }

    private class ListAdapter extends BaseListAdapter {

        public ListAdapter(Context context) {
            super(context);
        }

        @Override
        public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position, boolean partial) {
            if (holder.getItemViewType() == TYPE_SETTINGS) {
                TextSettingsCell textCell = (TextSettingsCell) holder.itemView;
                if (position == aboutRow) {
                    textCell.setTextAndValue(getString(R.string.FlexySettingsAbout), BuildVars.BUILD_VERSION_STRING, true);
                } else if (position == sourceCodeRow) {
                    textCell.setTextAndValue(getString(R.string.SourceCode), "GitHub", true);
                } else if (position == licenseRow) {
                    textCell.setTextAndValue(getString(R.string.FlexySettingsLicenseAction), "GPL-3.0", true);
                } else if (position == datacenterStatusRow) {
                    textCell.setText(getString(R.string.DatacenterStatus), false);
                }
            }
        }

        @Override
        public int getItemViewType(int position) {
            return TYPE_SETTINGS;
        }
    }
}
