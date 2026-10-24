package app.exteraless.player;

import android.content.Context;
import android.os.Build;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.WindowInsets;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.FrameLayout;
import android.widget.PopupMenu;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.MediaController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.R;
import org.telegram.messenger.LocaleController;
import org.telegram.ui.ActionBar.BaseFragment;

/** One ordinary child view in its fragment, never an overlay window or a playback owner. */
public final class SignatureMusicBubble extends FrameLayout {
    private final FrameLayout host;
    private final CoverImage art;
    private final RingPlayButton play;
    private final int slop;
    private float downX, downY, startX, startY;
    private boolean dragging;
    private boolean positioned;
    private MessageObject bound;
    private Boolean darkTheme;
    private boolean paused;
    private final OnLayoutChangeListener boundsListener = (v,l,t,r,b,ol,ot,or,ob) -> confine();

    private SignatureMusicBubble(FrameLayout host) {
        super(host.getContext());
        this.host = host;
        slop = ViewConfiguration.get(getContext()).getScaledTouchSlop();
        art = new CoverImage(getContext(), 26);
        art.setRadius(AndroidUtilities.dp(28));
        addView(art, new FrameLayout.LayoutParams(-1, -1));
        play = new RingPlayButton(getContext(), 10, 2, 11, 0, 8);
        FrameLayout.LayoutParams badge = new FrameLayout.LayoutParams(AndroidUtilities.dp(24), AndroidUtilities.dp(24), Gravity.BOTTOM | Gravity.RIGHT);
        addView(play, badge);
        setClickable(true);
        setFocusable(true);
        setContentDescription(LocaleController.getString(R.string.FlexyMusicExpand));
        setOnClickListener(v -> SignatureMusicPresentation.setCompact(false));
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
        SignatureMusicBubble bubble = new SignatureMusicBubble(host);
        host.addView(bubble, new FrameLayout.LayoutParams(AndroidUtilities.dp(56), AndroidUtilities.dp(56), Gravity.TOP | Gravity.LEFT));
        return bubble;
    }

    public void release() {
        host.removeOnLayoutChangeListener(boundsListener);
        host.removeView(this);
        art.setMessage(null);
    }

    public void update(boolean allowed, boolean dark) {
        MessageObject message = MediaController.getInstance().getPlayingMessageObject();
        boolean show = allowed && SignatureMusicPresentation.isCompact() && message != null && message.isMusic();
        setVisibility(show ? VISIBLE : GONE);
        if (!show) { play.setPlaying(false, false); return; }
        if (darkTheme == null || darkTheme != dark) {
            darkTheme = dark;
            PlayerColors colors = PlayerColors.fromSeed(0, dark);
            art.setColors(colors.primaryContainer, colors.onSurface);
            play.setColors(colors.primary, colors.surface, colors.onSurface);
        }
        if (bound != message) {
            bound = message;
            art.setMessage(message);
            play.setMessage(message);
            play.setPlaying(!MediaController.getInstance().isMessagePaused(), false);
        }
        boolean nowPaused = MediaController.getInstance().isMessagePaused();
        if (paused != nowPaused) { paused = nowPaused; play.setPlaying(!paused, false); }
        if (host.indexOfChild(this) != host.getChildCount() - 1) bringToFront();
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
                getParent().requestDisallowInterceptTouchEvent(true);
            }
            if (dragging) { setX(startX + dx); setY(startY + dy); confine(); return true; }
        } else if (event.getActionMasked() == MotionEvent.ACTION_UP || event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
            if (dragging) {
                dragging = false; setPressed(false);
                getParent().requestDisallowInterceptTouchEvent(false);
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
