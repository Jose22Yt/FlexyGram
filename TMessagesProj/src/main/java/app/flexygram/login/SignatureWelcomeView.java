/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.login;

import android.content.Context;
import android.content.res.Configuration;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** Static native welcome. No renderer, timers, loading gate or per-frame callback. */
public final class SignatureWelcomeView extends ScrollView {
    public final TextView startButton, languageButton;
    private final TextView title, subtitle;
    private final ImageView plane;
    public SignatureWelcomeView(Context context, Runnable start, Runnable language) {
        super(context);
        setFillViewport(true);
        setClipToPadding(false);
        LinearLayout content = new LinearLayout(context);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setGravity(Gravity.CENTER);
        content.setPadding(dp(24), dp(32), dp(24), dp(24));
        addView(content, new ScrollView.LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT));
        plane = new ImageView(context);
        plane.setScaleType(ImageView.ScaleType.FIT_CENTER);
        plane.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        content.addView(plane, new LinearLayout.LayoutParams(dp(96), dp(96)));
        title = label(context, 30); title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        if (android.os.Build.VERSION.SDK_INT >= 28) title.setAccessibilityHeading(true);
        content.addView(title, row(16));
        subtitle = label(context, 16); content.addView(subtitle, row(8));
        startButton = action(context, 17); startButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        startButton.setMinHeight(dp(52)); startButton.setPadding(dp(20), dp(12), dp(20), dp(12));
        startButton.setGravity(Gravity.CENTER); startButton.setClickable(true); startButton.setFocusable(true);
        content.addView(startButton, row(32));
        languageButton = action(context, 14); languageButton.setMinHeight(dp(48));
        languageButton.setClickable(true); languageButton.setFocusable(true);
        content.addView(languageButton, row(8));
        startButton.setOnClickListener(v -> start.run()); languageButton.setOnClickListener(v -> language.run());
        refresh();
    }
    private int dp(float value) { return AndroidUtilities.dp(value); }
    private LinearLayout.LayoutParams row(int top) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT);
        p.topMargin = dp(top); return p;
    }
    private TextView label(Context c, int sp) {
        TextView view = new TextView(c); view.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        view.setGravity(Gravity.CENTER); return view;
    }
    private TextView action(Context context, int sp) {
        android.widget.Button button = new android.widget.Button(context, null, 0);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER);
        button.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        button.setTypeface(Typeface.DEFAULT);
        button.setStateListAnimator(null);
        button.setElevation(0);
        return button;
    }
    public void refresh() {
        boolean dark = Theme.isCurrentThemeDark();
        setBackgroundColor(SignatureLoginPalette.background(dark));
        title.setText(LocaleController.getString(R.string.FlexySignatureName));
        subtitle.setText(LocaleController.getString(R.string.FlexySignatureTagline));
        startButton.setText(LocaleController.getString(R.string.FlexySignatureStart));
        languageButton.setText(LocaleController.getString(R.string.FlexySignatureLanguage));
        title.setTextColor(SignatureLoginPalette.ink(dark)); subtitle.setTextColor(SignatureLoginPalette.secondary(dark));
        startButton.setTextColor(dark ? 0xFF11151C : 0xFFFFFFFF);
        languageButton.setTextColor(SignatureLoginPalette.accent(dark));
        StateListDrawable states = new StateListDrawable();
        states.addState(new int[]{-android.R.attr.state_enabled}, button(SignatureLoginPalette.edge(dark)));
        states.addState(new int[]{android.R.attr.state_pressed}, button(SignatureLoginPalette.color(Theme.key_chats_actionPressedBackground)));
        states.addState(new int[]{}, button(SignatureLoginPalette.accent(dark)));
        startButton.setBackground(states);
        languageButton.setBackground(Theme.createSimpleSelectorRoundRectDrawable(dp(18), 0, dark ? 0x22FFFFFF : 0x11000000));
        SignatureIdentity.applyPlane(plane);
    }
    private GradientDrawable button(int color) {
        GradientDrawable d = new GradientDrawable(); d.setColor(color); d.setCornerRadius(dp(20)); return d;
    }
    @Override protected void onConfigurationChanged(Configuration configuration) {
        super.onConfigurationChanged(configuration); refresh();
    }
}
