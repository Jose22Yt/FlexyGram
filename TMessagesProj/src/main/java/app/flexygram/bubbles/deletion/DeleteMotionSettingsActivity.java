package app.flexygram.bubbles.deletion;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import app.flexygram.settings.signature.StylePreviewCard;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.RecyclerListView;

/** Same vertical, wallpaper-filled segments as composer/header selection. */
public final class DeleteMotionSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int GALLERY=331;
    private Gallery gallery;
    @Override protected String getActionBarTitle(){return LocaleController.getString(R.string.FlexyDeleteTitle);}
    @Override protected void updateRows(){super.updateRows();addRow("deleteMotionGallery");}
    @Override public View createView(Context context){View result=super.createView(context);listView.disableSections();listView.setItemAnimator(null);return result;}
    @Override protected void onItemClick(View view,int position,float x,float y){}
    @Override public void onResume(){super.onResume();if(gallery!=null)gallery.bind();}
    @Override public void onPause(){super.onPause();if(gallery!=null)gallery.stop();}
    private final class Gallery extends LinearLayout {
        private final StylePreviewCard[] cards=new StylePreviewCard[5];
        private final DeleteMotionPreview[] previews=new DeleteMotionPreview[5];
        Gallery(Context context){
            super(context);setOrientation(VERTICAL);setPadding(dp(12),dp(8),dp(12),dp(16));
            setTag(RecyclerListView.TAG_NOT_SECTION);setLayoutParams(new RecyclerView.LayoutParams(-1,-2));
            TextView hint=new TextView(context);hint.setText(LocaleController.getString(R.string.FlexyDeleteTapHint));hint.setTextSize(14);hint.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteGrayText));hint.setPadding(dp(8),dp(8),dp(8),dp(12));addView(hint,new LayoutParams(-1,-2));
            String[] labels=DeleteMotionSettings.labels();
            for(int i=0;i<cards.length;i++){
                final int style=i;previews[i]=new DeleteMotionPreview(context,style,resourcesProvider);
                cards[i]=new StylePreviewCard(context,resourcesProvider,labels[i],previews[i],()->{
                    for(DeleteMotionPreview preview:previews)if(preview!=null)preview.stop();
                    DeleteMotionSettings.set(context,style);bind();previews[style].play();
                },true);
                cards[i].setSegmentEdges(i==0,i==cards.length-1);LayoutParams lp=new LayoutParams(-1,-2);lp.topMargin=i==0?0:dp(4);addView(cards[i],lp);
            }
            TextView credit=new TextView(context);credit.setText(LocaleController.getString(R.string.FlexyDeleteAttribution));credit.setTextSize(12);credit.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteGrayText));credit.setPadding(dp(8),dp(12),dp(8),0);addView(credit,new LayoutParams(-1,-2));bind();
        }
        void stop(){for(DeleteMotionPreview preview:previews)if(preview!=null)preview.stop();}
        void bind(){int selected=DeleteMotionSettings.get(getContext());for(int i=0;i<cards.length;i++){cards[i].bind(i==selected);previews[i].bind(i==selected);}}
    }
    private static int dp(int value){return AndroidUtilities.dp(value);}
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int position){return GALLERY;}
        @Override protected boolean isSectionContent(int type){return false;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){return new RecyclerListView.Holder(gallery=new Gallery(parent.getContext()));}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){((Gallery)holder.itemView).bind();}
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return false;}
    };}
}
