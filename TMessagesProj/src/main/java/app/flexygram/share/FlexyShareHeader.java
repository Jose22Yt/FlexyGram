/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.share;
import android.content.Context;
import android.text.TextUtils;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;

/** Local presentation only. Has no sending, searching, account, file or network capability. */
public final class FlexyShareHeader extends FrameLayout {
    private final TextView preview,recipients;
    public FlexyShareHeader(Context c,Theme.ResourcesProvider provider,Runnable classic){
        super(c);
        float font=Math.max(1,c.getResources().getConfiguration().fontScale);
        int titleHeight=(int)Math.ceil(24*font),previewHeight=(int)Math.ceil(22*font),recipientsHeight=(int)Math.ceil(20*font);
        TextView title=text(c,17,Theme.getColor(Theme.key_dialogTextBlack,provider));title.setText("Flexy Share Sheet");
        addView(title,LayoutHelper.createFrame(-1,titleHeight,Gravity.TOP,16,6,94,0));
        TextView compatibility=text(c,12,Theme.getColor(Theme.key_dialogTextBlue,provider));compatibility.setGravity(Gravity.CENTER);compatibility.setText(LocaleController.getString(R.string.FlexyShareClassic));
        compatibility.setMinWidth(AndroidUtilities.dp(64));compatibility.setContentDescription(LocaleController.getString(R.string.FlexyShareClassic));
        addView(compatibility,LayoutHelper.createFrame(80,48,Gravity.TOP|Gravity.RIGHT,0,0,8,0));compatibility.setOnClickListener(v->classic.run());
        preview=text(c,14,Theme.getColor(Theme.key_dialogTextBlack,provider));addView(preview,LayoutHelper.createFrame(-1,previewHeight,Gravity.TOP,16,10+titleHeight,16,0));
        recipients=text(c,12,Theme.getColor(Theme.key_dialogTextGray2,provider));addView(recipients,LayoutHelper.createFrame(-1,recipientsHeight,Gravity.TOP,16,12+titleHeight+previewHeight,16,0));
        recipients(0,"");
    }
    public static int contentHeightDp(Context c){float f=Math.max(1,c.getResources().getConfiguration().fontScale);return 14+(int)Math.ceil(24*f)+(int)Math.ceil(22*f)+(int)Math.ceil(20*f);}
    private TextView text(Context c,int size,int color){TextView t=new TextView(c);t.setTextSize(size);t.setTextColor(color);t.setSingleLine(true);t.setEllipsize(TextUtils.TruncateAt.END);return t;}
    public void preview(CharSequence value){if(value==null)value="";preview.setText(value.length()>200?value.subSequence(0,200):value);}
    public void recipients(int count,CharSequence names){recipients.setText(count==0?LocaleController.getString(R.string.FlexyShareChooseRecipients):count+" · "+names);}
}
