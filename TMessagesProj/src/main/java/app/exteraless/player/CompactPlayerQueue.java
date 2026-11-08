package app.exteraless.player;

import android.content.Context;
import android.text.TextUtils;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.telegram.messenger.MediaController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.SharedConfig;
import org.telegram.messenger.R;
import org.telegram.messenger.LocaleController;
import org.telegram.ui.Components.LayoutHelper;
import java.util.ArrayList;

/** Two recycled upcoming rows, refreshed by the sheet's existing notifications, never by progress frames. */
final class CompactPlayerQueue extends LinearLayout {
    private final TextView heading;
    private final Row[] rows;
    CompactPlayerQueue(Context context,Runnable openQueue) {
        this(context,openQueue,2);
    }
    CompactPlayerQueue(Context context,Runnable openQueue,int visibleRows) {
        super(context);rows=new Row[Math.max(2,Math.min(12,visibleRows))];setOrientation(VERTICAL);
        heading=new TextView(context);heading.setTextSize(16);heading.setTypeface(org.telegram.messenger.AndroidUtilities.bold());
        heading.setText(LocaleController.getString(R.string.FlexyMusicQueueTitle));heading.setGravity(Gravity.CENTER_VERTICAL);
        heading.setOnClickListener(v->openQueue.run());heading.setFocusable(true);
        addView(heading,LayoutHelper.createLinear(-1,36));
        for(int i=0;i<rows.length;i++){rows[i]=new Row(context);addView(rows[i],LayoutHelper.createLinear(-1,52));}
    }
    void refresh(PlayerColors colors) {
        MediaController mc=MediaController.getInstance();java.util.List<MessageObject> list=mc.getMusicPlaybackOrder();
        boolean direct=SharedConfig.playOrderReversed;
        MessageObject playing=mc.getPlayingMessageObject();int current=-1;
        for(int i=0;i<list.size();i++)if(sameMessage(list.get(i),playing)){current=direct?i:list.size()-1-i;break;}
        int start=nextWindowStart(list.size(),current);
        heading.setTextColor(colors.onSurface);
        for(int i=0;i<rows.length;i++){
            int position=start+i;
            MessageObject message=position<list.size()?list.get(direct?position:list.size()-1-position):null;
            rows[i].bind(message,playing,colors);
        }
        setVisibility(start>=list.size()?GONE:VISIBLE);
    }
    static boolean sameMessage(MessageObject a,MessageObject b){return a!=null&&b!=null&&(a==b||a.getId()!=0&&a.currentAccount==b.currentAccount&&a.getId()==b.getId()&&a.getDialogId()==b.getDialogId());}
    static int nextWindowStart(int size,int current){return Math.max(0,Math.min(size,current+1));}
    private static final class Row extends LinearLayout {
        final CoverImage cover;final TextView title,artist;MessageObject message;PlayerColors lastColors;
        Row(Context context){
            super(context);setGravity(Gravity.CENTER_VERTICAL);
            cover=new CoverImage(context,18);cover.setRadius(org.telegram.messenger.AndroidUtilities.dp(8));addView(cover,LayoutHelper.createLinear(42,42));
            LinearLayout labels=new LinearLayout(context);labels.setOrientation(VERTICAL);
            title=new TextView(context);title.setTextSize(14);title.setSingleLine(true);title.setEllipsize(TextUtils.TruncateAt.END);
            artist=new TextView(context);artist.setTextSize(12);artist.setSingleLine(true);artist.setEllipsize(TextUtils.TruncateAt.END);
            labels.addView(title);labels.addView(artist);addView(labels,LayoutHelper.createLinear(0,-2,1f,12,0,8,0));
            setOnClickListener(v->{if(message==null)return;MediaController mc=MediaController.getInstance();if(mc.isPlayingMessage(message)){if(mc.isMessagePaused())mc.playMessage(message);else mc.pauseMessage(message);}else mc.findMessageInPlaylistAndPlay(message);});
        }
        void bind(MessageObject value,MessageObject playing,PlayerColors colors){
            if(message!=value)message=value;
            cover.setMessage(value);
            setVisibility(value==null?GONE:VISIBLE);if(value==null)return;
            if(!TextUtils.equals(title.getText(),value.getMusicTitle()))title.setText(value.getMusicTitle());
            if(!TextUtils.equals(artist.getText(),value.getMusicAuthor()))artist.setText(value.getMusicAuthor());
            boolean active=sameMessage(value,playing);title.setTextColor(active?colors.primary:colors.onSurface);artist.setTextColor(colors.onSurfaceVariant);
            cover.setColors(colors.primaryContainer,colors.onPrimaryContainer);
            if(lastColors!=colors){lastColors=colors;setBackground(org.telegram.ui.ActionBar.Theme.getSelectorDrawable(false));}
            setContentDescription(value.getMusicTitle()+", "+value.getMusicAuthor());
        }
    }
}
