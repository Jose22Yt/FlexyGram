package app.flexygram.elastic;

import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** Real interactive settings preview; shares the same observer and local fusion as the app. */
public final class ElasticPreviewView extends FrameLayout {
    private final TextView attach,send;
    public ElasticPreviewView(Context context){
        super(context);setLayoutParams(new RecyclerView.LayoutParams(-1,AndroidUtilities.dp(132)));setClipChildren(false);
        attach=pill(context,R.string.AccDescrAttachButton);send=pill(context,R.string.Send);
        LayoutParams left=new LayoutParams(AndroidUtilities.dp(112),AndroidUtilities.dp(52),Gravity.CENTER);
        left.rightMargin=AndroidUtilities.dp(62);addView(attach,left);
        LayoutParams right=new LayoutParams(AndroidUtilities.dp(112),AndroidUtilities.dp(52),Gravity.CENTER);
        right.leftMargin=AndroidUtilities.dp(62);addView(send,right);
        updateColors();ElasticFusionGroup.bind(this,attach,send);
    }
    private TextView pill(Context context,int label){
        TextView view=new TextView(context);view.setGravity(Gravity.CENTER);view.setText(LocaleController.getString(label));view.setTextSize(15);
        view.setOnClickListener(v->{});return view;
    }
    public void updateColors(){
        setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));
        for(TextView view:new TextView[]{attach,send}){
            view.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            GradientDrawable bg=new GradientDrawable();bg.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
            bg.setCornerRadius(AndroidUtilities.dp(26));view.setBackground(bg);
        }
    }
}
