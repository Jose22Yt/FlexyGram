package app.flexygram.settings.signature;

import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.SeekBar;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.composer.FlexyComposerConfig;
import app.flexygram.composer.FlexyComposerSettingsActivity;
import app.flexygram.composer.ComposerStyle;
import app.flexygram.header.HeaderConfig;
import app.flexygram.header.HeaderPreviewView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import tw.nekomimi.nekogram.ui.cells.HeaderCell;
import org.telegram.ui.Components.RecyclerListView;

/** Two composer choices or the available header styles; a tap uses the original setter. */
public final class ConversationStyleSettingsActivity extends SignatureMatteSettingsActivity {
    private static final int GALLERY = 310, POSITION = 311;
    private boolean header;
    private int galleryRow, layoutHeaderRow, levelRow, positionRow, resetPositionRow, infoRow;
    private Gallery gallery;
    public ConversationStyleSettingsActivity() {}
    public ConversationStyleSettingsActivity(boolean header){this.header=header;}
    private int dp(int value){return AndroidUtilities.dp(value);}
    @Override protected String getActionBarTitle(){return LocaleController.getString(header?R.string.FlexyInterfaceUpper:R.string.FlexyInterfaceLower);}
    @Override protected void updateRows(){
        super.updateRows();HeaderConfig.load();galleryRow=addRow();
        layoutHeaderRow=levelRow=positionRow=resetPositionRow=infoRow=-1;
        if(!header){
            layoutHeaderRow=addHeader("FlexyComposerLayoutSection");
            levelRow=addRow("flexyComposerLevel");
            positionRow=addRow("flexyComposerPosition");
            resetPositionRow=addRow();infoRow=addRow();
        }
    }
    private CharSequence[] sizes(){return new CharSequence[]{
        LocaleController.getString(R.string.FlexyComposerSizeNormal),
        LocaleController.getString(R.string.FlexyComposerSmall),
        LocaleController.getString(R.string.FlexyComposerSizeVeryCompact)};}
    private void refreshComposerChoices(){
        if(gallery!=null)gallery.bind();
        if(!header&&listAdapter!=null)listAdapter.notifyItemRangeChanged(levelRow,rowCount-levelRow);
    }
    @Override protected void onItemClick(View view,int position,float x,float y){
        if(header||position<0||!FlexyComposerConfig.compact())return;
        if(position==levelRow){
            showDialog(new AlertDialog.Builder(getParentActivity(),resourcesProvider)
                .setTitle(LocaleController.getString(R.string.FlexyComposerLevel))
                .setItems(sizes(),(dialog,which)->{FlexyComposerConfig.setLevel(which);refreshComposerChoices();}).create());
        }else if(position==resetPositionRow){
            FlexyComposerConfig.setPosition(0);
            listAdapter.notifyItemChanged(positionRow);
            if(gallery!=null)gallery.invalidatePreviews();
        }
    }
    @Override public View createView(Context context){View v=super.createView(context);if(header)listView.disableSections();listView.setItemAnimator(null);return v;}
    @Override public void saveSelfArgs(Bundle args){super.saveSelfArgs(args);args.putBoolean("headerStyleGallery",header);}
    @Override public void restoreSelfArgs(Bundle args){super.restoreSelfArgs(args);header=args.getBoolean("headerStyleGallery",false);}
    private final class Gallery extends LinearLayout {
        private final CompactStylePicker picker;
        private final View livePreview;
        Gallery(Context context){
            super(context);setOrientation(VERTICAL);
            setTag(RecyclerListView.TAG_NOT_SECTION);setLayoutParams(new RecyclerView.LayoutParams(-1,-2));
            FlexyComposerSettingsActivity composer=new FlexyComposerSettingsActivity();
            livePreview=header?new HeaderPreviewView(context):composer.createStylePreview(context,-1);
            picker=new CompactStylePicker(context,resourcesProvider,livePreview,2);
            addView(picker,new LayoutParams(-1,-2));
            int[] styles=header?new int[]{1,0,2,3,4}:new int[]{0,1};
            int[] labels=header?new int[]{R.string.FlexyStyleDefault,R.string.FlexyHeaderSignature,R.string.FlexyHeaderFusion,R.string.FlexyHeaderPortrait,R.string.FlexyHeaderFloating}:new int[]{R.string.FlexyStyleDefault,R.string.FlexyStyleCompact};
            for(int i=0;i<styles.length;i++){
                final int style=styles[i];
                View miniature=header?new HeaderPreviewView(context,style,true):composer.createStyleMiniature(context,style);
                picker.addChoice(style,LocaleController.getString(labels[i]),miniature,()->{
                    if(header){HeaderConfig.style(style);bind();}
                    else{FlexyComposerConfig.setStyle(style);refreshComposerChoices();}
                });
            }
            bind();
        }
        void bind(){
            picker.select(header?HeaderConfig.style():FlexyComposerConfig.compact()?1:0);
            if(livePreview instanceof HeaderPreviewView)((HeaderPreviewView)livePreview).settingsChanged();
            else livePreview.invalidate();
            picker.refreshMiniatures();
        }
        void invalidatePreviews(){livePreview.invalidate();picker.refreshMiniatures();}
    }
    private final class PositionCell extends LinearLayout implements Theme.Colorable {
        private final TextView title,value;
        private final app.flexygram.settings.FlexySignatureSlider slider;
        private boolean binding;
        PositionCell(Context context){
            super(context);setOrientation(VERTICAL);setPadding(dp(20),dp(8),dp(20),0);
            setLayoutParams(new RecyclerView.LayoutParams(-1,-2));
            title=new TextView(context);title.setTextSize(15);
            title.setText(LocaleController.getString(R.string.FlexyComposerPosition));
            addView(title,new LayoutParams(-1,-2));
            value=new TextView(context);value.setTextSize(13);addView(value,new LayoutParams(-1,-2));
            slider=new app.flexygram.settings.FlexySignatureSlider(context);
            slider.setMax(ComposerStyle.MAX_POSITION-ComposerStyle.MIN_POSITION);
            addView(slider,new LayoutParams(-1,dp(48)));
            slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
                public void onStartTrackingTouch(SeekBar bar){bar.getParent().requestDisallowInterceptTouchEvent(true);}
                public void onStopTrackingTouch(SeekBar bar){bar.getParent().requestDisallowInterceptTouchEvent(false);}
                public void onProgressChanged(SeekBar bar,int progress,boolean user){
                    if(binding||!user||!FlexyComposerConfig.compact())return;
                    FlexyComposerConfig.setPosition(progress+ComposerStyle.MIN_POSITION);
                    updateValue();if(gallery!=null)gallery.invalidatePreviews();
                }
            });
        }
        private void updateValue(){
            int position=FlexyComposerConfig.position();
            String text=position==0?LocaleController.getString(R.string.FlexyComposerPositionNeutral):
                LocaleController.formatString(position>0?R.string.FlexyComposerPositionUp:R.string.FlexyComposerPositionDown,Math.abs(position));
            value.setText(text);slider.setContentDescription(title.getText()+", "+text);
        }
        void bind(){
            binding=true;slider.setProgress(FlexyComposerConfig.position()-ComposerStyle.MIN_POSITION);binding=false;
            boolean enabled=FlexyComposerConfig.compact();slider.setEnabled(enabled);setAlpha(enabled?1f:.5f);
            updateValue();updateColors();
        }
        @Override public void updateColors(){
            title.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));
            value.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlueText));slider.updateColors();
        }
    }
    @Override protected BaseListAdapter createAdapter(Context context){return new MatteListAdapter(context){
        @Override public int getItemViewType(int position){return position==galleryRow?GALLERY:position==layoutHeaderRow?TYPE_HEADER:position==positionRow?POSITION:position==infoRow?TYPE_INFO_PRIVACY:TYPE_SETTINGS;}
        @Override protected boolean isSectionContent(int type){return type!=GALLERY&&type!=TYPE_HEADER&&super.isSectionContent(type);}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){
            if(type==GALLERY)return new RecyclerListView.Holder(gallery=new Gallery(parent.getContext()));
            if(type==POSITION)return new RecyclerListView.Holder(new PositionCell(parent.getContext()));
            RecyclerView.ViewHolder holder=super.onCreateViewHolder(parent,type);
            if(type==TYPE_HEADER)holder.itemView.setBackground(null);
            return holder;
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if(position==galleryRow){gallery=(Gallery)holder.itemView;gallery.bind();return;}
            if(position==layoutHeaderRow){((HeaderCell)holder.itemView).setText(LocaleController.getString(R.string.FlexyComposerLayoutSection));return;}
            if(position==positionRow){((PositionCell)holder.itemView).bind();return;}
            if(position==infoRow){((TextInfoPrivacyCell)holder.itemView).setText(LocaleController.getString(R.string.FlexyComposerAdjustmentsInfo));return;}
            TextSettingsCell cell=(TextSettingsCell)holder.itemView;
            if(position==levelRow)cell.setTextAndValue(LocaleController.getString(R.string.FlexyComposerLevel),sizes()[FlexyComposerConfig.level()].toString(),false);
            else cell.setText(LocaleController.getString(R.string.FlexyComposerPositionReset),false);
            cell.setEnabled(FlexyComposerConfig.compact(),null);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){int position=settingsRowPosition(holder);return !header&&position>=0&&FlexyComposerConfig.compact()&&(position==levelRow||position==resetPositionRow);}
    };}
}
