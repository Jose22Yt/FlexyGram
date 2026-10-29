/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;
import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;

/** Chats -> Message interactions. All controls are wired to actual visible UI behavior. */
public final class BubbleInteractionSettingsActivity extends SignatureMatteSettingsActivity {
    private int panelRow, bounceRow, infoRow, tapRow, tapPanelRow, resetRow;
    private final int[] parameterRows=new int[3];
    private static final int SLIDER=112;
    @Override protected String getActionBarTitle() {
        return LocaleController.getString(R.string.FlexyContextInteractions);
    }
    @Override protected void updateRows() {
        super.updateRows();
        tapRow=addRow("flexyTapAnimation");
        for(int i=0;i<3;i++)parameterRows[i]=addRow("flexyTapParameter"+i);
        tapPanelRow=addRow("flexyTapPanel");
        resetRow=addRow("flexyTapReset");
        panelRow = addRow("flexyContextPanel");
        bounceRow = addRow("flexyContextBounce");
        infoRow = addRow();
    }
    @Override protected BaseListAdapter createAdapter(Context context) { return new Adapter(context); }
    @Override protected void onItemClick(View view, int position, float x, float y) {
        Context context = getParentActivity();
        if (context == null) return;
        if(position==tapRow){BubbleInteractionSettings.tapAnimation(context,!BubbleInteractionSettings.tapAnimation(context));}
        else if(position==tapPanelRow){BubbleInteractionSettings.tapPanel(context,!BubbleInteractionSettings.tapPanel(context));}
        else if(position==resetRow){BubbleInteractionSettings.resetTap(context);listAdapter.notifyDataSetChanged();return;}
        else if (position == panelRow) {
            BubbleInteractionSettings.setSignaturePanel(context,
                    !BubbleInteractionSettings.signaturePanel(context));
        } else if (position == bounceRow) {
            BubbleInteractionSettings.setSpringBounce(context,
                    !BubbleInteractionSettings.springBounce(context));

        } else return;
        listAdapter.notifyItemChanged(position);
    }
    private int parameter(int row){for(int i=0;i<3;i++)if(parameterRows[i]==row)return i;return -1;}
    private final class TapSlider extends android.widget.LinearLayout {
        final android.widget.TextView title;final android.widget.SeekBar slider;int which;boolean binding;
        TapSlider(Context c){super(c);setOrientation(VERTICAL);setPadding(20,8,20,4);
            title=new android.widget.TextView(c);title.setTextSize(16);title.setTextColor(getThemedColor(org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));addView(title);
            slider=new app.flexygram.settings.FlexySignatureSlider(c);slider.setMax(100);addView(slider,new LayoutParams(-1,org.telegram.messenger.AndroidUtilities.dp(48)));
            slider.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){
                public void onStartTrackingTouch(android.widget.SeekBar b){getParent().requestDisallowInterceptTouchEvent(true);}
                public void onStopTrackingTouch(android.widget.SeekBar b){getParent().requestDisallowInterceptTouchEvent(false);}
                public void onProgressChanged(android.widget.SeekBar b,int value,boolean user){if(user&&!binding)BubbleInteractionSettings.parameter(c,which,value);show(value);}
            });
        }
        void show(int value){String label=LocaleController.getString(which==0?R.string.FlexyTapCompression:which==1?R.string.FlexyTapRebound:R.string.FlexyTapRecovery)+" · "+value+" %";title.setText(label);slider.setContentDescription(label);}
        void bind(int index){which=index;binding=true;int v=index==0?BubbleInteractionSettings.compression(getContext()):index==1?BubbleInteractionSettings.rebound(getContext()):BubbleInteractionSettings.recovery(getContext());slider.setProgress(v);show(v);binding=false;}
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context) { super(context); }
        @Override public int getItemViewType(int position) {
            return parameter(position)>=0?SLIDER:position==resetRow?TYPE_SETTINGS:position == infoRow ? TYPE_INFO_PRIVACY : TYPE_CHECK;
        }
        @Override public RecyclerView.ViewHolder onCreateViewHolder(android.view.ViewGroup parent,int type){if(type==SLIDER)return new org.telegram.ui.Components.RecyclerListView.Holder(new TapSlider(parent.getContext()));return super.onCreateViewHolder(parent,type);}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            Context context = holder.itemView.getContext();
            if(parameter(position)>=0){((TapSlider)holder.itemView).bind(parameter(position));return;}
            if(position==resetRow){((org.telegram.ui.Cells.TextSettingsCell)holder.itemView).setText(LocaleController.getString(R.string.Reset),true);return;}
            if (position == infoRow) {
                ((TextInfoPrivacyCell) holder.itemView).setText(
                        LocaleController.getString(R.string.FlexyContextDescription));
                return;
            }
            TextCheckCell cell = (TextCheckCell) holder.itemView;
            if(position==tapRow){cell.setTextAndCheck(LocaleController.getString(R.string.FlexyTapAnimation),BubbleInteractionSettings.tapAnimation(context),true);}
            else if(position==tapPanelRow){cell.setTextAndCheck(LocaleController.getString(R.string.FlexyTapPanel),BubbleInteractionSettings.tapPanel(context),true);}
            else if (position == panelRow) {
                cell.setTextAndCheck(LocaleController.getString(R.string.FlexyContextPanel),
                        BubbleInteractionSettings.signaturePanel(context), true);
            } else if (position == bounceRow) {
                cell.setTextAndCheck(LocaleController.getString(R.string.FlexyContextBounce),
                        BubbleInteractionSettings.springBounce(context), false);

            }
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) {
            int position = holder.getAdapterPosition();
            return position==tapRow || position==tapPanelRow || position==resetRow || position == panelRow || position == bounceRow;
        }
    }
}
