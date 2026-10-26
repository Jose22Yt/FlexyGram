package app.exteraless.player;

import android.content.Context;
import android.os.Build;
import android.graphics.drawable.GradientDrawable;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.WindowInsets;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.FrameLayout;
import android.widget.PopupMenu;
import android.widget.TextView;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.MediaController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.R;
import org.telegram.messenger.LocaleController;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;

/** One ordinary child view in its fragment, never an overlay window or a playback owner. */
public final class SignatureMusicBubble extends FrameLayout {
    private final FrameLayout host;
    private final CoverImage art;
    private final RingPlayButton play;
    private final TextView title;
    private final TextView artist;
    private final TextView close;
    private final GradientDrawable pill = new GradientDrawable();
    private final int slop;
    private float downX, downY, startX, startY;
    private boolean dragging;
    private boolean positioned;
    private MessageObject bound;
    private Boolean darkTheme;
    private int themeAccent;
    private boolean paused;
    private boolean released;
    private boolean expanded;
    private final OnLayoutChangeListener boundsListener = (v,l,t,r,b,ol,ot,or,ob) -> confine();

    private SignatureMusicBubble(FrameLayout host) {
        super(host.getContext());
        this.host = host;
        slop = ViewConfiguration.get(getContext()).getScaledTouchSlop();
        art = new CoverImage(getContext(), 26);
        art.setRadius(AndroidUtilities.dp(28));
        addView(art, new FrameLayout.LayoutParams(AndroidUtilities.dp(56), AndroidUtilities.dp(56), Gravity.LEFT | Gravity.TOP));
        pill.setCornerRadius(AndroidUtilities.dp(28));
        setBackground(pill);
        title = new TextView(getContext());
        title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        title.setSingleLine(true);
        title.setEllipsize(TextUtils.TruncateAt.END);
        title.setGravity(Gravity.CENTER_VERTICAL);
        FrameLayout.LayoutParams titleParams = new FrameLayout.LayoutParams(AndroidUtilities.dp(116), AndroidUtilities.dp(23), Gravity.LEFT | Gravity.TOP);
        titleParams.leftMargin = AndroidUtilities.dp(64);
        titleParams.topMargin = AndroidUtilities.dp(7);
        addView(title, titleParams);
        title.setOnClickListener(v -> SignatureMusicPresentation.setCompact(false));
        title.setVisibility(GONE);
        artist = new TextView(getContext());
        artist.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        artist.setSingleLine(true);
        artist.setEllipsize(TextUtils.TruncateAt.END);
        FrameLayout.LayoutParams artistParams = new FrameLayout.LayoutParams(AndroidUtilities.dp(116), AndroidUtilities.dp(20), Gravity.LEFT | Gravity.TOP);
        artistParams.leftMargin = AndroidUtilities.dp(64);
        artistParams.topMargin = AndroidUtilities.dp(29);
        addView(artist, artistParams);
        artist.setOnClickListener(v -> SignatureMusicPresentation.setCompact(false));
        artist.setVisibility(GONE);
        play = new RingPlayButton(getContext(), 10, 2, 11, 0, 8);
        FrameLayout.LayoutParams badge = new FrameLayout.LayoutParams(AndroidUtilities.dp(32), AndroidUtilities.dp(56), Gravity.RIGHT | Gravity.TOP);
        badge.rightMargin = AndroidUtilities.dp(36);
        addView(play, badge);
        play.setOnClickListener(v -> {
            MessageObject mo = MediaController.getInstance().getPlayingMessageObject();
            if (mo == null) return;
            if (MediaController.getInstance().isMessagePaused()) MediaController.getInstance().playMessage(mo);
            else MediaController.getInstance().pauseMessage(mo);
            update(true, darkTheme != null && darkTheme);
        });
        close = new TextView(getContext());
        close.setGravity(Gravity.CENTER);
        close.setText("×");
        close.setTextSize(TypedValue.COMPLEX_UNIT_SP, 25);
        addView(close, new FrameLayout.LayoutParams(AndroidUtilities.dp(36), -1, Gravity.RIGHT | Gravity.TOP));
        close.setOnClickListener(v -> {
            SignatureMusicPresentation.setCompact(false);
            MediaController.getInstance().cleanupPlayer(true, true);
        });
        close.setContentDescription(LocaleController.getString(R.string.AccDescrClosePlayer));
        close.setVisibility(GONE);
        setClickable(true);
        setFocusable(true);
        setContentDescription(LocaleController.getString(R.string.FlexyMusicExpand));
        setOnClickListener(v -> { if (expanded) SignatureMusicPresentation.setCompact(false); else setExpanded(true); });
        art.setOnClickListener(v -> { if (expanded) setExpanded(false); else setExpanded(true); });
        setOnLongClickListener(v -> {
            PopupMenu menu = new PopupMenu(getContext(), this);
            menu.getMenu().add(LocaleController.getString(R.string.FlexyMusicExpand)).setOnMenuItemClickListener(item -> {
                SignatureMusicPresentation.setCompact(false); return true;
            });
            menu.getMenu().add(LocaleController.getString(R.string.AccDescrClosePlayer)).setOnMenuItemClickListener(item -> {
                SignatureMusicPresentation.setCompact(false);
                MediaController.getInstance().cleanupPlayer(true, true); return true;
            });
            menu.show();
            return true;
        });
        setVisibility(GONE);
        host.addOnLayoutChangeListener(boundsListener);
    }

    public static SignatureMusicBubble attach(BaseFragment fragment) {
        if (fragment == null || !(fragment.getFragmentView() instanceof FrameLayout)) return null;
        FrameLayout host = (FrameLayout) fragment.getFragmentView();
        // Do not mutate the child array during an ancestor's window detach.
        for (int i = 0; i < host.getChildCount(); i++) {
            View child = host.getChildAt(i);
            if (child instanceof SignatureMusicBubble && ((SignatureMusicBubble) child).released) {
                SignatureMusicBubble bubble = (SignatureMusicBubble) child;
                bubble.released = false;
                host.addOnLayoutChangeListener(bubble.boundsListener);
                return bubble;
            }
        }
        SignatureMusicBubble bubble = new SignatureMusicBubble(host);
        host.addView(bubble, new FrameLayout.LayoutParams(AndroidUtilities.dp(56), AndroidUtilities.dp(56), Gravity.TOP | Gravity.LEFT));
        return bubble;
    }

    public void release() {
        release(false);
    }
    public void releaseFromWindow() { release(true); }
    private void release(boolean windowDetaching) {
        if (released) return;
        released = true;
        host.removeOnLayoutChangeListener(boundsListener);
        cancelLongPress(); dragging = false; setPressed(false); setVisibility(GONE);
        host.requestDisallowInterceptTouchEvent(false);
        play.setPlaying(false, false);
        bound = null;
        art.setMessage(null);
        // The fragment root owns this inert child. attach() reuses it, keeping
        // dispatchDetachedFromWindow's children snapshot stable and bounded.
        if (!windowDetaching && getParent() == host) host.removeView(this);
    }

    public void update(boolean allowed, boolean dark) {
        if (released) return;
        MessageObject message = MediaController.getInstance().getPlayingMessageObject();
        boolean show = allowed && SignatureMusicPresentation.isCompact() && message != null && message.isMusic();
        setVisibility(show ? VISIBLE : GONE);
        if (!show) { play.setPlaying(false, false); return; }
        int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        if (darkTheme == null || darkTheme != dark || themeAccent != accent) {
            darkTheme = dark;
            themeAccent = accent;
            PlayerColors colors = PlayerColors.fromSignatureTheme(dark);
            art.setColors(colors.primaryContainer, colors.onSurface);
            play.setColors(colors.primary, colors.surface, colors.onSurface);
            pill.setColor(colors.surfaceContainer);
            pill.setStroke(AndroidUtilities.dp(1), colors.outlineVariant);
            title.setTextColor(colors.onSurface);
            artist.setTextColor(colors.onSurfaceVariant);
            close.setTextColor(colors.onSurface);
        }
        if (bound != message) {
            bound = message;
            art.setMessage(message);
            title.setText(message.getMusicTitle());
            artist.setText(message.getMusicAuthor());
            play.setMessage(message);
            play.setPlaying(!MediaController.getInstance().isMessagePaused(), false);
        }
        boolean nowPaused = MediaController.getInstance().isMessagePaused();
        if (paused != nowPaused) { paused = nowPaused; play.setPlaying(!paused, false); }
        if (host.indexOfChild(this) != host.getChildCount() - 1) bringToFront();
        confine();
    }

    private void setExpanded(boolean value) {
        if (expanded == value) return;
        expanded = value;
        FrameLayout.LayoutParams params = (FrameLayout.LayoutParams) getLayoutParams();
        params.width = AndroidUtilities.dp(value ? 256 : 56);
        setLayoutParams(params);
        title.setVisibility(value ? VISIBLE : GONE);
        artist.setVisibility(value ? VISIBLE : GONE);
        close.setVisibility(value ? VISIBLE : GONE);
        FrameLayout.LayoutParams badge = (FrameLayout.LayoutParams) play.getLayoutParams();
        badge.width = AndroidUtilities.dp(value ? 36 : 24);
        badge.height = AndroidUtilities.dp(value ? 56 : 24);
        badge.rightMargin = AndroidUtilities.dp(value ? 36 : 0);
        badge.gravity = value ? Gravity.RIGHT | Gravity.TOP : Gravity.RIGHT | Gravity.BOTTOM;
        play.setLayoutParams(badge);
        setContentDescription(LocaleController.getString(R.string.FlexyMusicExpand));
        art.setContentDescription(LocaleController.getString(value ? R.string.FlexyMusicCompact : R.string.FlexyMusicExpand));
        confine();
    }

    private void confine() {
        int top = AndroidUtilities.dp(96), bottom = AndroidUtilities.dp(112), side = AndroidUtilities.dp(12);
        if (Build.VERSION.SDK_INT >= 30) {
            WindowInsets insets = host.getRootWindowInsets();
            if (insets != null) {
                android.graphics.Insets safe = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
                top = Math.max(top, safe.top + AndroidUtilities.dp(56));
                bottom = Math.max(bottom, safe.bottom + AndroidUtilities.dp(64));
                side = Math.max(side, Math.max(safe.left, safe.right));
            }
        }
        if (host.getWidth() == 0 || host.getHeight() == 0) return;
        float x = positioned ? getX() : host.getWidth() - AndroidUtilities.dp(68);
        float y = positioned ? getY() : host.getHeight() * .45f;
        setX(SignatureMusicStyle.clamp(x, side, host.getWidth() - getLayoutParams().width - side));
        setY(SignatureMusicStyle.clamp(y, Math.min(top, Math.max(0, host.getHeight() - getLayoutParams().height)),
                host.getHeight() - getLayoutParams().height - bottom));
        positioned = true;
    }

    @Override public boolean onInterceptTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            downX = event.getRawX(); downY = event.getRawY();
            startX = getX(); startY = getY(); dragging = false;
        } else if (action == MotionEvent.ACTION_MOVE) {
            float dx = event.getRawX() - downX, dy = event.getRawY() - downY;
            if (dx * dx + dy * dy > slop * slop) {
                dragging = true;
                cancelLongPress();
                if (getParent() != null) getParent().requestDisallowInterceptTouchEvent(true);
                return true;
            }
        }
        return super.onInterceptTouchEvent(event);
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
            downX = event.getRawX(); downY = event.getRawY();
            startX = getX(); startY = getY(); dragging = false;
        } else if (event.getActionMasked() == MotionEvent.ACTION_MOVE) {
            float dx = event.getRawX() - downX, dy = event.getRawY() - downY;
            if (!dragging && dx * dx + dy * dy > slop * slop) {
                dragging = true;
                cancelLongPress();
                MotionEvent cancel = MotionEvent.obtain(event.getDownTime(), event.getEventTime(), MotionEvent.ACTION_CANCEL, 0, 0, 0);
                super.onTouchEvent(cancel);
                cancel.recycle();
                if (getParent() != null) getParent().requestDisallowInterceptTouchEvent(true);
            }
            if (dragging) { setX(startX + dx); setY(startY + dy); confine(); return true; }
        } else if (event.getActionMasked() == MotionEvent.ACTION_UP || event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
            if (dragging) {
                dragging = false; setPressed(false);
                if (getParent() != null) getParent().requestDisallowInterceptTouchEvent(false);
                return true;
            }
        }
        return super.onTouchEvent(event);
    }

    @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info) {
        super.onInitializeAccessibilityNodeInfo(info);
        info.setClassName("android.widget.Button");
        info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_LONG_CLICK);
    }
}
