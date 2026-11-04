package app.flexygram.settings.signature;

import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.composer.FlexyComposerConfig;
import app.flexygram.composer.FlexyComposerSettingsActivity;
import app.flexygram.header.HeaderConfig;
import app.flexygram.header.HeaderPreviewView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.RecyclerListView;

/** Two composer choices or the four existing header styles; a tap uses the original setter. */
public final class ConversationStyleSettingsActivity extends SignatureMatteSettingsActivity {
    private boolean header;
    public ConversationStyleSettingsActivity() {}
    public ConversationStyleSettingsActivity(boolean header){this.header=header;}
    private int dp(int value){return AndroidUtilities.dp(value);}
    @Override protected String getActionBarTitle(){return LocaleController.getString(header?R.string.FlexyInterfaceUpper:R.string.FlexyInterfaceLower);}
    @Override protected void updateRows(){super.updateRows();HeaderConfig.load();rowCount=1;}
    @Override protected void onItemClick(View view,int position,float x,float y){}
    @Override public View createView(Context context){View v=super.createView(context);listView.disableSections();listView.setItemAnimator(null);return v;}
    @Override public void saveSelfArgs(Bundle args){super.saveSelfArgs(args);args.putBoolean("headerStyleGallery",header);}
    @Override public void restoreSelfArgs(Bundle args){super.restoreSelfArgs(args);header=args.getBoolean("headerStyleGallery",false);}
    private final class Gallery extends LinearLayout {
        private final TextView hint;
        private final StylePreviewCard[] choices;
        private final int[] styles;
        Gallery(Context context){
            super(context);setOrientation(VERTICAL);setPadding(dp(12),dp(8),dp(12),dp(12));
            hint=new TextView(context);hint.setTextSize(14);hint.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteGrayText2));hint.setPadding(dp(8),dp(8),dp(8),dp(16));
            hint.setText(LocaleController.getString(header?R.string.FlexyStyleSwipeHint:R.string.FlexyStyleTapHint));addView(hint,new LayoutParams(-1,-2));
            styles=header?new int[]{1,0,2,3}:new int[]{0,1};choices=new StylePreviewCard[styles.length];
            int[] labels=header?new int[]{R.string.FlexyStyleDefault,R.string.FlexyHeaderSignature,R.string.FlexyHeaderFusion,R.string.FlexyHeaderPortrait}:new int[]{R.string.FlexyStyleDefault,R.string.FlexyStyleCompact};
            LinearLayout strip=new LinearLayout(context);strip.setOrientation(header?HORIZONTAL:VERTICAL);
            HorizontalScrollView scroll=header?new HorizontalScrollView(context):null;
            if(header){scroll.setHorizontalScrollBarEnabled(false);scroll.setClipToPadding(false);scroll.addView(strip,new ViewGroup.LayoutParams(-2,-2));addView(scroll,new LayoutParams(-1,-2));}
            else addView(strip,new LayoutParams(-1,-2));
            for(int i=0;i<styles.length;i++){
                final int index=i;
                View preview=header?new HeaderPreviewView(context,styles[i]):new FlexyComposerSettingsActivity().createStylePreview(context,styles[i]);
                choices[i]=new StylePreviewCard(context,resourcesProvider,LocaleController.getString(labels[i]),preview,()->{
                    if(header)HeaderConfig.style(styles[index]);else FlexyComposerConfig.setStyle(styles[index]);bind();
                });
                int width=header?Math.max(dp(220),Math.min(context.getResources().getDisplayMetrics().widthPixels-dp(56),dp(420))):-1;
                LayoutParams params=new LayoutParams(width,-2);if(header)params.setMarginEnd(dp(12));else params.bottomMargin=dp(12);strip.addView(choices[i],params);
            }
            bind();
            if(header){final HorizontalScrollView viewport=scroll;post(()->{for(int i=0;i<styles.length;i++)if(styles[i]==HeaderConfig.style())viewport.scrollTo(choices[i].getLeft(),0);});}
        }
        @Override protected void dispatchDraw(android.graphics.Canvas canvas){int color=getThemedColor(Theme.key_windowBackgroundWhiteGrayText2);if(hint.getCurrentTextColor()!=color)hint.setTextColor(color);super.dispatchDraw(canvas);}
        void bind(){int selected=header?HeaderConfig.style():FlexyComposerConfig.compact()?1:0;for(int i=0;i<styles.length;i++)choices[i].bind(styles[i]==selected);}
    }
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int position){return 310;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){return new RecyclerListView.Holder(new Gallery(parent.getContext()));}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){((Gallery)holder.itemView).bind();}
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return false;}
    };}
}
