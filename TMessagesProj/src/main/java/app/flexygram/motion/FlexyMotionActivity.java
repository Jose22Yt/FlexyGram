/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.graphics.Canvas;
import android.view.*;
import android.widget.*;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Components.RecyclerListView;

/** HyperStudio motion page. Only live controls for migrated components; never changes system scales. */
public final class FlexyMotionActivity extends SignatureMatteSettingsActivity {
    private static final int PREVIEW=120;
    private int profiles,flash,flow,signature,reduced,shadow,preview,advanced,speed,stiffness,damping,press,reset,info;
    @Override protected String getActionBarTitle(){return getString(R.string.FlexyMotionTitle);}
    @Override protected void updateRows(){super.updateRows();profiles=addRow();flash=addRow("motionFlash");flow=addRow("motionFlow");signature=addRow("motionSignature");reduced=addRow("motionReduced");shadow=addRow();preview=addRow();advanced=addRow();speed=addRow("motionSpeed");stiffness=addRow("motionStiffness");damping=addRow("motionDamping");press=addRow("motionPress");reset=addRow("motionReset");info=addRow();}
    @Override protected BaseListAdapter createAdapter(Context c){return new Adapter(c);}
    private void refresh(){if(listView!=null&&listView.getAdapter()!=null)listView.getAdapter().notifyDataSetChanged();}
    @Override protected void onItemClick(View v,int position,float x,float y){
        Context c=getParentActivity();if(c==null)return;
        if(position==flash||position==flow||position==signature){FlexyMotionSettings.setProfile(c,position==flash?FlexyMotionProfile.FLASH:position==flow?FlexyMotionProfile.FLOW:FlexyMotionProfile.SIGNATURE);refresh();}
        else if(position==reduced){FlexyMotionSettings.setReduceMotion(c,!FlexyMotionSettings.reduceMotion(c));refresh();}
        else if(position==reset){FlexyMotionSettings.setProfile(c,FlexyMotionSettings.profile(c));refresh();}
        else if(position==speed||position==stiffness||position==damping||position==press){
            float[] values=position==speed?new float[]{.5f,.75f,1,1.25f,1.5f,2}:position==stiffness?new float[]{200,390,560,750,1000}:position==damping?new float[]{.55f,.68f,.8f,.92f,1,1.2f}:new float[]{.94f,.95f,.965f,.975f,.99f,1};
            String[] labels=new String[values.length];for(int i=0;i<values.length;i++)labels[i]=Float.toString(values[i]);
            showDialog(new AlertDialog.Builder(c,getResourceProvider()).setTitle(getString(position==speed?R.string.FlexyMotionSpeed:position==stiffness?R.string.FlexyMotionStiffness:position==damping?R.string.FlexyMotionDamping:R.string.FlexyMotionPress)).setItems(labels,(dialog,which)->{FlexyMotionSettings.State s=FlexyMotionSettings.state(c);float value=values[which];FlexyMotionSettings.tune(c,position==speed?value:s.speed,position==stiffness?value:s.stiffness,position==damping?value:s.damping,position==press?value:s.pressedScale);refresh();}).create());
        }
    }
    private final class Adapter extends MatteListAdapter {
        Adapter(Context c){super(c);}
        @Override public int getItemViewType(int p){return p==profiles||p==advanced?TYPE_HEADER:p==shadow?TYPE_SHADOW:p==preview?PREVIEW:p==reduced?TYPE_CHECK:p==info?TYPE_INFO_PRIVACY:TYPE_SETTINGS;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){if(type!=PREVIEW)return super.onCreateViewHolder(parent,type);return new RecyclerListView.Holder(new Preview(parent.getContext()));}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){
            FlexyMotionSettings.State s=FlexyMotionSettings.state(h.itemView.getContext());
            if(p==profiles||p==advanced)((tw.nekomimi.nekogram.ui.cells.HeaderCell)h.itemView).setText(getString(p==profiles?R.string.FlexyMotionProfiles:R.string.FlexyMotionPhysics));
            else if(p==reduced)((TextCheckCell)h.itemView).setTextAndCheck(getString(R.string.FlexyMotionReduced),s.reduceMotion,false);
            else if(p==info)((org.telegram.ui.Cells.TextInfoPrivacyCell)h.itemView).setText(getString(R.string.FlexyMotionCoverage));
            else if(p!=shadow&&p!=preview){String title,value="";
                if(p==flash||p==flow||p==signature){FlexyMotionProfile profile=p==flash?FlexyMotionProfile.FLASH:p==flow?FlexyMotionProfile.FLOW:FlexyMotionProfile.SIGNATURE;title="Flexy "+(p==flash?"Flash":p==flow?"Flow":"Signature");if(s.profile==profile)value=getString(R.string.FlexyMotionSelected);}
                else {title=getString(p==speed?R.string.FlexyMotionSpeed:p==stiffness?R.string.FlexyMotionStiffness:p==damping?R.string.FlexyMotionDamping:p==press?R.string.FlexyMotionPress:R.string.FlexyMotionReset);if(p!=reset)value=Float.toString(p==speed?s.speed:p==stiffness?s.stiffness:p==damping?s.damping:s.pressedScale);}
                ((TextSettingsCell)h.itemView).setTextAndValue(title,value,p!=reset);
            }
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){return h.getItemViewType()==TYPE_CHECK||h.getItemViewType()==TYPE_SETTINGS;}
    }
    private static final class Preview extends Button {
        private final FlexyTouchFeedback feedback;
        Preview(Context c){super(c);setText(getString(R.string.FlexyMotionPreview));setMinHeight(org.telegram.messenger.AndroidUtilities.dp(56));setOnClickListener(v->{});feedback=new FlexyTouchFeedback(this);setLayoutParams(new RecyclerView.LayoutParams(-1,-2));}
        @Override public boolean dispatchTouchEvent(MotionEvent e){feedback.onTouch(e);return super.dispatchTouchEvent(e);}
        @Override public void draw(Canvas c){int save=c.save();if(feedback!=null)feedback.transform(c);super.draw(c);c.restoreToCount(save);}
        @Override protected void onDetachedFromWindow(){if(feedback!=null)feedback.reset();super.onDetachedFromWindow();}
    }
}
