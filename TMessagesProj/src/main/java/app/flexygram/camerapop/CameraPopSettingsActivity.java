/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

import android.app.TimePickerDialog;
import android.content.Context;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Locale;
import org.telegram.messenger.DialogObject;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.UsersSelectActivity;

/** Native per-account settings and Telegram's searchable multi-chat selector. */
public final class CameraPopSettingsActivity extends SignatureMatteSettingsActivity {
    private int enabled,selected,immediate,reminders,interval,duration,names,muted,quiet,start,end,demo,info;
    private CameraPopConfig config;
    @Override protected String getActionBarTitle() {return LocaleController.getString(R.string.CameraPopTitle);}
    @Override protected void updateRows() {
        super.updateRows();config=new CameraPopConfig(currentAccount);
        enabled=addRow("cameraPopEnabled");selected=addRow("cameraPopSelected");
        immediate=addRow("cameraPopImmediate");reminders=addRow("cameraPopReminders");
        interval=addRow("cameraPopInterval");duration=addRow("cameraPopDuration");
        names=addRow("cameraPopNames");muted=addRow("cameraPopRespectMuted");
        quiet=addRow("cameraPopQuiet");start=addRow("cameraPopQuietStart");end=addRow("cameraPopQuietEnd");
        demo=addRow("cameraPopDemo");info=addRow("cameraPopInfo");
    }
    private String text(int id) {return LocaleController.getString(id);}
    private void changed() {
        CameraPopRuntime.configurationChanged(currentAccount);config=new CameraPopConfig(currentAccount);
        if(listAdapter!=null)listAdapter.notifyDataSetChanged();
    }
    private void choose(String key,int title,int[] values,String[] labels) {
        showDialog(new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle(text(title))
                .setItems(labels,(d,index)->{config.set(key,values[index]);changed();}).create());
    }
    private void time(String key,int minute) {
        showDialog(new TimePickerDialog(getParentActivity(),(v,h,m)->{config.set(key,h*60+m);changed();},minute/60,minute%60,true));
    }
    @Override protected void onItemClick(View view,int position,float x,float y) {
        if(getParentActivity()==null)return;
        if(position==enabled)config.set("enabled",!config.enabled);
        else if(position==immediate)config.set("immediate",!config.immediate);
        else if(position==reminders)config.set("reminders",!config.reminders);
        else if(position==names)config.set("names",!config.names);
        else if(position==muted)config.set("respect_muted",!config.respectMuted);
        else if(position==quiet)config.set("quiet",!config.quiet);
        else if(position==selected) {
            UsersSelectActivity picker=new UsersSelectActivity(true,new ArrayList<>(config.selected),0);
            picker.setCurrentAccount(currentAccount);picker.noChatTypes=true;picker.allowSelf=false;
            picker.setDelegate((ids,flags)->{
                HashSet<Long> chosen=new HashSet<>();
                for(long id:ids)if(DialogObject.isUserDialog(id)||DialogObject.isChatDialog(id))chosen.add(id);
                config.select(chosen);changed();
            });presentFragment(picker);return;
        } else if(position==interval) {
            choose("interval",R.string.CameraPopInterval,new int[]{5,15,30},new String[]{
                    LocaleController.formatPluralString("Minutes",5),LocaleController.formatPluralString("Minutes",15),LocaleController.formatPluralString("Minutes",30)});return;
        } else if(position==duration) {
            choose("duration",R.string.CameraPopDuration,new int[]{2,4,6,10},new String[]{
                    LocaleController.formatPluralString("Seconds",2),LocaleController.formatPluralString("Seconds",4),
                    LocaleController.formatPluralString("Seconds",6),LocaleController.formatPluralString("Seconds",10)});return;
        } else if(position==start) {time("quiet_start",config.quietStart);return;}
        else if(position==end) {time("quiet_end",config.quietEnd);return;}
        else if(position==demo) {CameraPopRuntime.demonstrate();return;}
        else return;
        changed();
    }
    @Override public void onResume() {super.onResume();config=new CameraPopConfig(currentAccount);if(listAdapter!=null)listAdapter.notifyDataSetChanged();}
    private String clock(int minutes) {return String.format(Locale.US,"%02d:%02d",minutes/60,minutes%60);}
    @Override protected BaseListAdapter createAdapter(Context context) {return new MatteListAdapter(context) {
        @Override public int getItemViewType(int p) {
            return p==info?TYPE_INFO_PRIVACY:p==enabled||p==immediate||p==reminders||p==names||p==muted||p==quiet?TYPE_CHECK:TYPE_SETTINGS;
        }
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int p,boolean partial) {
            if(p==info) {((org.telegram.ui.Cells.TextInfoPrivacyCell)holder.itemView).setText(text(R.string.CameraPopInfo));return;}
            int title;boolean check=false;String value="";
            if(p==enabled){title=R.string.CameraPopEnabled;check=config.enabled;}
            else if(p==selected){title=R.string.CameraPopSelected;value=Integer.toString(config.selected.size());}
            else if(p==immediate){title=R.string.CameraPopImmediate;check=config.immediate;}
            else if(p==reminders){title=R.string.CameraPopReminders;check=config.reminders;}
            else if(p==interval){title=R.string.CameraPopInterval;value=LocaleController.formatPluralString("Minutes",config.intervalMinutes);}
            else if(p==duration){title=R.string.CameraPopDuration;value=LocaleController.formatPluralString("Seconds",config.durationSeconds);}
            else if(p==names){title=R.string.CameraPopNames;check=config.names;}
            else if(p==muted){title=R.string.CameraPopRespectMuted;check=config.respectMuted;}
            else if(p==quiet){title=R.string.CameraPopQuiet;check=config.quiet;}
            else if(p==start){title=R.string.CameraPopQuietStart;value=clock(config.quietStart);}
            else if(p==end){title=R.string.CameraPopQuietEnd;value=clock(config.quietEnd);}
            else title=R.string.CameraPopDemo;
            if(holder.itemView instanceof TextCheckCell)((TextCheckCell)holder.itemView).setTextAndCheck(text(title),check,true);
            else ((TextSettingsCell)holder.itemView).setTextAndValue(text(title),value,p!=demo);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder) {return settingsRowPosition(holder)!=info;}
    };}
}
