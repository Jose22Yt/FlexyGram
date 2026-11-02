/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.deletion;

import android.app.Activity;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import android.content.Context;
import android.graphics.Color;
import android.graphics.RectF;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ScrollView;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.TextView;
import java.util.Collections;

/** Self-contained native selector + live demo. Add one entry in Animaciones de mensajes. */
public final class DeleteMotionSettingsDialog {
    private DeleteMotionSettingsDialog() {}
    private static int dp(Context c, float n) { return Math.round(c.getResources().getDisplayMetrics().density*n); }

    public static void show(Activity activity) {
        if (activity == null || activity.isFinishing()) return;
        LinearLayout root = new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(activity,18),dp(activity,8),dp(activity,18),dp(activity,12));

        TextView details = new TextView(activity);
        details.setText(LocaleController.getString(R.string.FlexyDeleteDescription));
        details.setTextSize(13f);
        details.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
        root.addView(details,new LinearLayout.LayoutParams(-1,-2));

        RadioGroup styles = new RadioGroup(activity);
        styles.setOrientation(RadioGroup.VERTICAL);
        String[] labels = DeleteMotionSettings.labels();
        for(int i=0;i<labels.length;i++) {
            RadioButton radio = new RadioButton(activity);
            radio.setId(2000+i);radio.setText(labels[i]);radio.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));radio.setTextSize(15f);
            radio.setPadding(0,dp(activity,6),0,dp(activity,6));
            styles.addView(radio,new RadioGroup.LayoutParams(-1,-2));
        }
        styles.check(2000+DeleteMotionSettings.get(activity));
        styles.setOnCheckedChangeListener((g,id) -> {
            if(id>=2000 && id<=2004)DeleteMotionSettings.set(activity,id-2000);
        });
        root.addView(styles,new LinearLayout.LayoutParams(-1,-2));

        TextView previewTitle=new TextView(activity);
        previewTitle.setText(LocaleController.getString(R.string.FlexyDeletePreview));previewTitle.setTextSize(14f);previewTitle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        LinearLayout.LayoutParams titleParams=new LinearLayout.LayoutParams(-1,-2);
        titleParams.topMargin=dp(activity,8);
        root.addView(previewTitle,titleParams);

        FrameLayout preview = new FrameLayout(activity);
        preview.setClipChildren(true);
        preview.setClipToPadding(true);
        GradientDrawable background = new GradientDrawable();
        background.setColor(0x142279CE);background.setCornerRadius(dp(activity,12));
        preview.setBackground(background);
        LinearLayout.LayoutParams previewParams=new LinearLayout.LayoutParams(-1,dp(activity,175));
        previewParams.topMargin=dp(activity,8);
        root.addView(preview,previewParams);

        TextView sample = new TextView(activity);
        sample.setText(LocaleController.getString(R.string.FlexyDeleteSample));
        sample.setTextSize(14f);sample.setTextColor(Theme.getColor(Theme.key_chat_messageTextOut));
        sample.setPadding(dp(activity,12),dp(activity,9),dp(activity,12),dp(activity,9));
        GradientDrawable bubble = new GradientDrawable();
        bubble.setColor(Theme.getColor(Theme.key_chat_outBubble));bubble.setCornerRadius(dp(activity,16));
        sample.setBackground(bubble);
        FrameLayout.LayoutParams bubbleParams=new FrameLayout.LayoutParams(-2,-2,Gravity.CENTER);
        preview.addView(sample,bubbleParams);

        Button play=new Button(activity);
        play.setText(LocaleController.getString(R.string.FlexyDeletePlay));
        LinearLayout.LayoutParams playParams=new LinearLayout.LayoutParams(-1,-2);
        playParams.topMargin=dp(activity,8);
        root.addView(play,playParams);

        final boolean[] playing={false};
        play.setOnClickListener(v -> {
            if(playing[0] || !preview.isAttachedToWindow())return;
            int selected=DeleteMotionSettings.get(activity);
            if(selected == DeleteMotionSettings.DEFAULT)return;
            if(!sample.isShown() || sample.getWidth()<1 || sample.getHeight()<1)return;
            playing[0]=true;
            DeleteMotionOverlay.Target t=new DeleteMotionOverlay.Target(
                    sample,new RectF(0,0,sample.getWidth(),sample.getHeight()));
            DeleteMotionOverlay.runNativeDelete(preview,Collections.singletonList(t),selected,
                    () -> sample.setVisibility(View.INVISIBLE));
            sample.postDelayed(() -> {
                sample.setVisibility(View.VISIBLE);
                playing[0]=false;
            },600L);
        });

        ScrollView scroll = new ScrollView(activity);
        scroll.addView(root);
        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setTitle(LocaleController.getString(R.string.FlexyDeleteTitle))
                .setView(scroll)
                .setPositiveButton(LocaleController.getString(R.string.Done),(d,which) -> {})
                .create();
        dialog.show();
    }
}
