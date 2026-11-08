package app.exteraless.player;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;

import android.animation.ValueAnimator;
import org.telegram.messenger.BuildConfig;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Outline;
import android.graphics.RectF;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewOutlineProvider;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.core.graphics.ColorUtils;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.FileLoader;
import org.telegram.messenger.MediaController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.R;
import org.telegram.messenger.UserConfig;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.CubicBezierInterpolator;
import org.telegram.ui.Components.LayoutHelper;

public class PlayerMiniView extends FrameLayout implements NotificationCenter.NotificationCenterDelegate {

    public static final int HEIGHT_DP = 60;

    private SignatureMusicHost signatureHost;
    private final BaseFragment fragment;
    private final Theme.ResourcesProvider resourcesProvider;
    private boolean dark;
    private int seed;
    private final FrameLayout card;
    private MusicBlurSurface blurSurface;
    private MusicProgressView progress;
    private final GradientDrawable cardBg = new GradientDrawable();
    private final CoverImage cover;
    private final TextView titleView;
    private final TextView artistView;
    private final RingPlayButton playButton;
    private final ImageView nextButton;
    private final ImageView closeButton;
    private final PlayerIcon nextIcon = PlayerIcon.fill(PlayerIcon.NEXT,24);
    private final PlayerIcon closeIcon = PlayerIcon.stroke(PlayerIcon.CLOSE, 22);
    private PlayerColors colors;
    private ValueAnimator showAnimator;
    private MessageObject current;
    private boolean shown;
    private float showProgress;
    private float hostFactor = 1f;
    private float baseTranslation;
    private Runnable offsetListener;

    public PlayerMiniView(Context context, BaseFragment fragment, Theme.ResourcesProvider resourcesProvider) {
        super(context);
        this.fragment = fragment;
        this.resourcesProvider = resourcesProvider;
        dark = PlayerColors.isDark(resourcesProvider);
        seed = PlayerColors.fallbackSeed(resourcesProvider);
        colors = BuildConfig.CONNECTED_ALPHA?PlayerColors.fromSignatureTheme(dark,resourcesProvider):PlayerColors.fromSeed(seed, dark);
        setClipChildren(false);
        setClipToPadding(false);

        card = new FrameLayout(context);
        LinearLayout row = new LinearLayout(context);
        row.setOrientation(LinearLayout.HORIZONTAL); row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(10),0,dp(6),0);
        card.addView(row, LayoutHelper.createFrame(-1,-1));
        cardBg.setCornerRadius(dp(20));
        card.setBackground(cardBg);
        if (BuildConfig.CONNECTED_ALPHA) { blurSurface = new MusicBlurSurface(card, dp(22)); card.setBackground(blurSurface); }
        progress = new MusicProgressView(context, false);
        card.addView(progress, LayoutHelper.createFrame(-1,2,Gravity.BOTTOM,dp(0),0,0,0));
        if (!BuildConfig.CONNECTED_ALPHA) {
            card.setOutlineProvider(new ViewOutlineProvider() {
                @Override
                public void getOutline(View view, Outline outline) {
                    outline.setRoundRect(0, 0, view.getWidth(), view.getHeight(), dp(20));
                }
            });
            card.setClipToOutline(true);
            card.setElevation(dp(1));
        }
        card.setOnClickListener(v -> Md3Player.open(fragment, this));
        card.setOnLongClickListener(v->{if(signatureHost!=null&&signatureHost.canCompact()){SignatureMusicPresentation.setCompact(true);return true;}return false;});
        card.setContentDescription(getString(R.string.OEPlayerOpen));
        addView(card, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, HEIGHT_DP, Gravity.BOTTOM, 12, 0, 12, 12));

        cover = new CoverImage(context, 22);
        cover.setRadius(dp(12));
        row.addView(cover, LayoutHelper.createLinear(44, 44));

        LinearLayout texts = new LinearLayout(context);
        texts.setOrientation(LinearLayout.VERTICAL);
        titleView = new TextView(context);
        titleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        titleView.setTypeface(AndroidUtilities.bold());
        titleView.setSingleLine(true);
        titleView.setEllipsize(TextUtils.TruncateAt.END);
        texts.addView(titleView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));
        artistView = new TextView(context);
        artistView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        artistView.setSingleLine(true);
        artistView.setEllipsize(TextUtils.TruncateAt.END);
        artistView.setAlpha(0.8f);
        texts.addView(artistView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 2, 0, 0));
        row.addView(texts, LayoutHelper.createLinear(0, LayoutHelper.WRAP_CONTENT, 1f, 12, 0, 20, 0));

        playButton = new RingPlayButton(context, 20, 3, 22, 1.3f, 12);
        if (BuildConfig.CONNECTED_ALPHA) {
            playButton.setFillCircle(true);
            playButton.setShowRing(false);
        } else {
            playButton.setShowRing(true);
        }
        playButton.setOnClickListener(v -> {
            MediaController mc = MediaController.getInstance();
            MessageObject mo = mc.getPlayingMessageObject();
            if (mo == null || mc.isDownloadingCurrentMessage()) {
                return;
            }
            if (mc.isMessagePaused()) {
                mc.playMessage(mo);
            } else {
                mc.pauseMessage(mo);
            }
        });
        row.addView(playButton, LayoutHelper.createLinear(48, 48));

        nextButton = new ImageView(context);
        nextButton.setScaleType(ImageView.ScaleType.CENTER);
        nextButton.setImageDrawable(nextIcon);
        nextButton.setContentDescription(getString(R.string.Next));
        nextButton.setOnClickListener(v -> {
            MediaController.getInstance().playNextMessage();
        });
        row.addView(nextButton, LayoutHelper.createLinear(48, 48));

        closeButton = new ImageView(context);
        closeButton.setScaleType(ImageView.ScaleType.CENTER);
        closeButton.setImageDrawable(closeIcon);
        closeButton.setContentDescription(getString(R.string.AccDescrClosePlayer));
        closeButton.setOnClickListener(v -> {
            SignatureMusicPresentation.setCompact(false);
            MediaController.getInstance().cleanupPlayer(true, true);
        });
        closeButton.setOnLongClickListener(v -> { MediaController.getInstance().cleanupPlayer(true, true); return true; });
        row.addView(closeButton, LayoutHelper.createLinear(48, 48));

        applyColors(colors);
        setVisibility(GONE);
    }

    @Override protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        boolean showNext = MeasureSpec.getSize(widthMeasureSpec) >= dp(320);
        nextButton.setVisibility(showNext ? VISIBLE : GONE);
        if (blurSurface != null) {
            int controlsWidth = dp(6 + 48 * (showNext ? 3 : 2));
            int segmentGap = dp(12);
            blurSurface.setSegments(controlsWidth, segmentGap);
            FrameLayout.LayoutParams line = (FrameLayout.LayoutParams) progress.getLayoutParams();
            line.width = Math.max(0, MeasureSpec.getSize(widthMeasureSpec) - dp(24) - controlsWidth - segmentGap - dp(24));
            line.leftMargin = dp(12);
            line.bottomMargin = dp(6);
        }
        super.onMeasure(widthMeasureSpec, heightMeasureSpec);
    }

    @Override public void draw(Canvas canvas) { if (!MusicBlurSurface.isCapturing()) super.draw(canvas); }

    public boolean canTransition() {
        return isAttachedToWindow() && getVisibility() == VISIBLE && shown && showProgress >= 1f && hostFactor >= 0.99f && card.getWidth() > 0;
    }

    public void getCardRect(RectF out) {
        locate(card, out);
    }

    public void getCoverRect(RectF out) {
        locate(cover, out);
    }

    private static void locate(View view, RectF out) {
        int[] loc = new int[2];
        view.getLocationOnScreen(loc);
        out.set(loc[0], loc[1], loc[0] + view.getWidth(), loc[1] + view.getHeight());
    }

    public float getCardRadius() {
        return dp(20);
    }

    public float getCoverRadius() {
        return dp(12);
    }

    public int getCardColor() {
        return colors.primaryContainer;
    }

    public Bitmap getCoverBitmap() {
        return cover.getImageReceiver().getBitmap();
    }

    public Bitmap captureCard() {
        int w = card.getWidth();
        int h = card.getHeight();
        if (w <= 0 || h <= 0) {
            return null;
        }
        int visibility = cover.getVisibility();
        try {
            Bitmap bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            Canvas canvas = new Canvas(bitmap);
            cover.setVisibility(INVISIBLE);
            card.setPressed(false);
            card.jumpDrawablesToCurrentState();
            card.draw(canvas);
            return bitmap;
        } catch (Throwable e) {
            return null;
        } finally {
            cover.setVisibility(visibility);
        }
    }

    public void setTransitionHidden(boolean hidden) {
        card.setAlpha(hidden ? 0f : 1f);
    }

    public void setOffsetListener(Runnable listener) {
        offsetListener = listener;
    }

    public float getVisibleOffset() {
        return (dp(HEIGHT_DP) + dp(8)) * showProgress * hostFactor;
    }

    public int getTargetOffset() {
        return shown && hostFactor > 0.5f ? dp(HEIGHT_DP) + dp(8) : 0;
    }

    public void setHostPosition(float translation, float factor) {
        baseTranslation = translation;
        float old = hostFactor;
        hostFactor = factor;
        applyTransform();
        if (old != factor) {
            notifyOffset();
        }
    }

    private void applyTransform() {
        float p = showProgress * hostFactor;
        setTranslationY(baseTranslation + dp(24) * (1f - p));
        setAlpha(p);
        setVisibility(p > 0f ? VISIBLE : GONE);
    }

    private void notifyOffset() {
        if (offsetListener != null) {
            offsetListener.run();
        }
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        if (blurSurface != null) blurSurface.attach();
        NotificationCenter.getGlobalInstance().addObserver(this, NotificationCenter.didSetNewTheme);
        for (int a = 0; a < UserConfig.MAX_ACCOUNT_COUNT; a++) {
            NotificationCenter nc = NotificationCenter.getInstance(a);
            nc.addObserver(this, NotificationCenter.messagePlayingDidStart);
            nc.addObserver(this, NotificationCenter.messagePlayingDidReset);
            nc.addObserver(this, NotificationCenter.messagePlayingPlayStateChanged);
            nc.addObserver(this, NotificationCenter.messagePlayingProgressDidChanged);
            nc.addObserver(this, NotificationCenter.fileLoaded);
            nc.addObserver(this, NotificationCenter.audioInfoLoaded);
        }
        if (BuildConfig.CONNECTED_ALPHA) {
            signatureHost = new SignatureMusicHost(fragment, resourcesProvider, () -> update(false));
            signatureHost.attach();
        }
        update(false);
    }

    @Override
    protected void onDetachedFromWindow() {
        if (blurSurface != null) blurSurface.detach();
        if (signatureHost != null) { signatureHost.detachFromWindow(); signatureHost = null; }
        super.onDetachedFromWindow();
        NotificationCenter.getGlobalInstance().removeObserver(this, NotificationCenter.didSetNewTheme);
        if (showAnimator != null) { showAnimator.cancel(); showAnimator = null; }
        for (int a = 0; a < UserConfig.MAX_ACCOUNT_COUNT; a++) {
            NotificationCenter nc = NotificationCenter.getInstance(a);
            nc.removeObserver(this, NotificationCenter.messagePlayingDidStart);
            nc.removeObserver(this, NotificationCenter.messagePlayingDidReset);
            nc.removeObserver(this, NotificationCenter.messagePlayingPlayStateChanged);
            nc.removeObserver(this, NotificationCenter.messagePlayingProgressDidChanged);
            nc.removeObserver(this, NotificationCenter.fileLoaded);
            nc.removeObserver(this, NotificationCenter.audioInfoLoaded);
        }
    }

    @Override
    public void didReceivedNotification(int id, int account, Object... args) {
        if (signatureHost != null) signatureHost.update(Md3Player.miniEnabled());
        if (id == NotificationCenter.messagePlayingProgressDidChanged) {
            playButton.progressChanged();
            progress.invalidate();
        } else if (id == NotificationCenter.audioInfoLoaded) {
            MessageObject mo = current;
            if (mo != null && PlayerArt.isPlaying(mo)) {
                cover.setMessage(mo);
            }
        } else if (id == NotificationCenter.fileLoaded) {
            MessageObject mo = current;
            if (mo != null && mo.getDocument() != null && TextUtils.equals((String) args[0], FileLoader.getAttachFileName(mo.getDocument()))) {
                cover.setMessage(mo);
            }
        } else {
            update(true);
        }
    }

    private void checkThemeColors() {
        boolean themeDark = PlayerColors.isDark(resourcesProvider);
        int themeSeed = PlayerColors.fallbackSeed(resourcesProvider);
        if (BuildConfig.CONNECTED_ALPHA) { PlayerColors next = PlayerColors.fromSignatureTheme(themeDark, resourcesProvider); if (next != colors) applyColors(next); }
        if (themeDark != dark || themeSeed != seed) {
            dark = themeDark;
            seed = themeSeed;
            applyColors(BuildConfig.CONNECTED_ALPHA?PlayerColors.fromSignatureTheme(dark,resourcesProvider):PlayerColors.fromSeed(seed, dark));
        }
    }

    public void update(boolean animated) {
        checkThemeColors();
        MessageObject mo = MediaController.getInstance().getPlayingMessageObject();
        boolean want = Md3Player.miniEnabled() && mo != null && mo.isMusic() && mo.getId() != 0;
        if (signatureHost != null) {
            signatureHost.update(want);

            if (signatureHost.canCompact() && SignatureMusicPresentation.isCompact()) want = false;
        }
        if(!want&&(mo==null||!mo.isMusic())&&current!=null){current=null;cover.setMessage(null);playButton.setMessage(null);progress.setMessage(null);}
        if (want) {
            bind(mo);
        }
        playButton.setPlaying(want && !MediaController.getInstance().isMessagePaused(), animated);
        setShown(want, animated);
    }

    private void bind(MessageObject mo) {
        if (current != mo || !TextUtils.equals(titleView.getText(), mo.getMusicTitle())
                || !TextUtils.equals(artistView.getText(), mo.getMusicAuthor())) {
            titleView.setText(mo.getMusicTitle());
            artistView.setText(mo.getMusicAuthor());
            cover.setMessage(mo);
        }
        current = mo;
        progress.setMessage(mo);
        artistView.setVisibility(getResources().getConfiguration().fontScale > 1.5f ? GONE : VISIBLE);
        card.setContentDescription(mo.getMusicTitle() + ", " + mo.getMusicAuthor());
        playButton.setMessage(mo);
        playButton.setContentDescription(getString(MediaController.getInstance().isMessagePaused() ? R.string.AccActionPlay : R.string.AccActionPause));
    }

    private void setShown(boolean value, boolean animated) {
        if (shown == value && (showAnimator != null || showProgress == (value ? 1f : 0f))) {
            return;
        }
        shown = value;
        if (showAnimator != null) {
            showAnimator.cancel();
            showAnimator = null;
        }
        float target = value ? 1f : 0f;
        if (!animated || !isAttachedToWindow()) {
            showProgress = target;
            applyTransform();
            notifyOffset();
            return;
        }
        showAnimator = ValueAnimator.ofFloat(showProgress, target);
        showAnimator.addUpdateListener(a -> {
            showProgress = (float) a.getAnimatedValue();
            applyTransform();
            notifyOffset();
        });
        showAnimator.setDuration(180);
        showAnimator.setInterpolator(value ? new CubicBezierInterpolator(0.05, 0.7, 0.1, 1) : new CubicBezierInterpolator(0.3, 0, 0.8, 0.15));
        showAnimator.start();
    }

    private void applyColors(PlayerColors c) {
        colors = c;
        if (blurSurface != null) blurSurface.setColors(c);
        progress.setColors(c);
        cardBg.setColor(c.primaryContainer);
        cardBg.setStroke(dp(1), c.outlineVariant);
        if (Build.VERSION.SDK_INT >= 28 && !BuildConfig.CONNECTED_ALPHA) {
            card.setOutlineSpotShadowColor(c.shadow());
            card.setOutlineAmbientShadowColor(c.shadow());
        }
        cover.setColors(c.secondaryContainer, c.onSecondaryContainer);
        titleView.setTextColor(BuildConfig.CONNECTED_ALPHA?c.onSurface:c.onPrimaryContainer);
        artistView.setTextColor(BuildConfig.CONNECTED_ALPHA?c.onSurfaceVariant:c.onPrimaryContainer);
        nextIcon.setColor(c.onPrimaryContainer);
        closeIcon.setColor(c.onPrimaryContainer);
        int ripple = ColorUtils.setAlphaComponent(c.onPrimaryContainer, 0x1f);
        nextButton.setBackground(Theme.createSelectorDrawable(ripple, Theme.RIPPLE_MASK_CIRCLE_20DP));
        closeButton.setBackground(Theme.createSelectorDrawable(ripple, Theme.RIPPLE_MASK_CIRCLE_20DP));
        playButton.setBackground(Theme.createSelectorDrawable(ripple, Theme.RIPPLE_MASK_CIRCLE_20DP));
        int accent = BuildConfig.CONNECTED_ALPHA ? c.primary : c.onPrimaryContainer;
        if (BuildConfig.CONNECTED_ALPHA) {
            playButton.setFillIconColor(c.onPrimary);
        }
        playButton.setColors(accent, ColorUtils.setAlphaComponent(accent, 46), accent);
        if(!BuildConfig.CONNECTED_ALPHA)card.setForeground(Theme.createSelectorDrawable(ripple, Theme.RIPPLE_MASK_ALL));
    }
}
