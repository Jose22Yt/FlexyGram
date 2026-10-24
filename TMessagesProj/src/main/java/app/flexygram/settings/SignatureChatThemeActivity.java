package app.flexygram.settings;

import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.ThemeActivity;
import org.telegram.ui.WallpapersListActivity;

/** Routes to Telegram's existing theme and wallpaper editors without duplicating their state. */
public final class SignatureChatThemeActivity extends SignatureMatteSettingsActivity {
    private int themeRow, wallpaperRow;
    @Override protected void updateRows() {
        super.updateRows(); themeRow = addRow("signatureChatTheme"); wallpaperRow = addRow("signatureChatWallpaper");
    }
    @Override protected String getActionBarTitle() { return getString(R.string.FlexyThemeWallpaper); }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position == themeRow) presentFragment(new ThemeActivity(ThemeActivity.THEME_TYPE_THEMES_BROWSER));
        else if (position == wallpaperRow) presentFragment(new WallpapersListActivity(WallpapersListActivity.TYPE_ALL));
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) { return TYPE_SETTINGS; }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            ((TextSettingsCell)holder.itemView).setText(getString(position == themeRow ? R.string.BrowseThemes : R.string.ChangeChatBackground), position == themeRow);
        }
    }
}
