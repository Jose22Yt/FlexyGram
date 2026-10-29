/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.navigation;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.R;
import org.telegram.messenger.UserConfig;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Components.RecyclerListView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import app.exteraless.appearance.AppearanceConfig;
import tw.nekomimi.nekogram.helpers.MainTabsHelper;
import xyz.nextalone.nagram.NaConfig;

/** Apariencia -> Barra inferior. Only exposes destinations implemented by MainTabsActivity. */
public final class LiquidNavigationSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int PREVIEW = 111, SLIDER = 112;
    private int previewRow, enabledRow, elasticRow, opacityRow;
    private int contactsRow, profileRow, callsRow, feedRow, noticeRow;
    private LiquidNavigationPreviewView preview;
    @Override protected String getActionBarTitle() { return getString(R.string.FlexyLiquidNavTitle); }
    @Override protected void updateRows() {
        super.updateRows();
        previewRow = addRow();
        enabledRow = addRow("flexyLiquidEnabled");
        elasticRow = addRow("flexyLiquidElastic");
        opacityRow = addRow("flexyLiquidOpacity");
        contactsRow = addRow("flexyLiquidContacts");
        profileRow = addRow("flexyLiquidProfile");
        callsRow = addRow("flexyLiquidCalls");
        feedRow = addRow("flexyLiquidFeed");
        noticeRow = addRow();
    }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        if (position == enabledRow) {
            LiquidNavigationConfig.enabled(!LiquidNavigationConfig.enabled());
        } else if (position == contactsRow) {
            NaConfig.INSTANCE.getMainTabsHideContacts()
                    .setConfigBool(!MainTabsHelper.isContactsTabHidden());
        } else if (position == profileRow) {
            NaConfig.INSTANCE.getMainTabsHideProfile()
                    .setConfigBool(!MainTabsHelper.isProfileTabHidden());
        } else if (position == callsRow) {
            final int account = UserConfig.selectedAccount;
            final boolean enabled = MainTabsHelper.isCallsTabShown(account);
            if (!enabled) NaConfig.INSTANCE.getMainTabsHideCallsSettings().setConfigBool(false);
            UserConfig.getInstance(account).setShowCallsTab(!enabled);
        } else if (position == feedRow) {
            AppearanceConfig.showFeedTab.setConfigBool(!AppearanceConfig.showFeedTab());
        } else return;
        if (preview != null) preview.settingsChanged();
        if (listAdapter != null) listAdapter.notifyDataSetChanged();
    }
    private final class MotionSlider extends LinearLayout implements Theme.Colorable {
        final TextView title; final SeekBar seek;
        boolean editing, opacity;
        MotionSlider(Context c) {
            super(c); setOrientation(VERTICAL); setPadding(dp(20),dp(10),dp(20),dp(5));
            title=new TextView(c); title.setTextSize(16);
            title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            addView(title,new LayoutParams(-1,-2));
            seek=new app.flexygram.settings.FlexySignatureSlider(c);
            seek.setMax(100);addView(seek,new LayoutParams(-1,dp(48)));
            seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
                @Override public void onStartTrackingTouch(SeekBar b) {
                    if(b.getParent()!=null)b.getParent().requestDisallowInterceptTouchEvent(true);
                }
                @Override public void onStopTrackingTouch(SeekBar b) {
                    if(b.getParent()!=null)b.getParent().requestDisallowInterceptTouchEvent(false);
                }
                @Override public void onProgressChanged(SeekBar b,int value,boolean fromUser) {
                    if(!editing && fromUser) {
                        if(opacity) LiquidNavigationConfig.opacity(value);
                        else LiquidNavigationConfig.elasticity(value);
                        if(preview!=null) preview.settingsChanged();
                    }
                    setLabel(value);
                }
            });
        }
        @Override public void updateColors() {
            title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            seek.invalidate();
        }
        private void setLabel(int n) {
            title.setText(getString(opacity?R.string.FlexyLiquidNavOpacity
                    :R.string.FlexyLiquidNavElasticity)+" · "+n+"%");
        }
        void bind(boolean isOpacity) {
            editing=true;opacity=isOpacity;
            int value=opacity?LiquidNavigationConfig.opacity():Math.round(LiquidNavigationConfig.elasticity()*100);
            seek.setProgress(value);setLabel(value);editing=false;
        }
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int position) {
            if (position == previewRow) return PREVIEW;
            if (position == elasticRow || position == opacityRow) return SLIDER;
            if (position == noticeRow) return TYPE_INFO_PRIVACY;
            return TYPE_CHECK;
        }
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type) {
            if(type == PREVIEW) {
                preview=new LiquidNavigationPreviewView(parent.getContext());
                return new RecyclerListView.Holder(preview);
            }
            if(type == SLIDER) return new RecyclerListView.Holder(new MotionSlider(parent.getContext()));
            return super.onCreateViewHolder(parent,type);
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int position,boolean partial) {
            if(position == previewRow){h.itemView.invalidate();return;}
            if(position == elasticRow || position == opacityRow) {
                ((MotionSlider)h.itemView).bind(position==opacityRow);return;
            }
            if(position == noticeRow) {
                ((TextInfoPrivacyCell)h.itemView).setText(
                    getString(R.string.FlexyLiquidNavChatsFixed)+"\n"+
                    getString(R.string.FlexyLiquidNavReloadHint));
                return;
            }
            final TextCheckCell check=(TextCheckCell)h.itemView;
            if(position == enabledRow)
                check.setTextAndCheck(getString(R.string.FlexyLiquidNavEnabled),
                    LiquidNavigationConfig.enabled(),true);
            else if(position == contactsRow)
                check.setTextAndCheck(getString(R.string.FlexyLiquidNavContacts),
                    !MainTabsHelper.isContactsTabHidden(),true);
            else if(position == profileRow)
                check.setTextAndCheck(getString(R.string.FlexyLiquidNavProfile),
                    !MainTabsHelper.isProfileTabHidden(),true);
            else if(position == callsRow)
                check.setTextAndCheck(getString(R.string.FlexyLiquidNavCalls),
                    MainTabsHelper.isCallsTabShown(UserConfig.selectedAccount),true);
            else if(position == feedRow)
                check.setTextAndCheck(getString(R.string.FlexyLiquidNavFeed),
                    AppearanceConfig.showFeedTab(),false);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder h) {
            int pos=h.getAdapterPosition();
            return pos==enabledRow||pos==contactsRow||pos==profileRow||pos==callsRow||pos==feedRow;
        }
    }
}
