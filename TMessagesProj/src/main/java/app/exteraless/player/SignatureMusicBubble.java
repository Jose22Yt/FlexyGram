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
    private java.lang.ref.WeakReference<BaseFragment> owner=new java.lang.ref.WeakReference<>(null);
    private final CoverImage art;
    private final RingPlayButton play;
    private final TextView title;
    private final TextView artist;
    private final TextView close;
    private final MusicBlurSurface pill;
    private final MusicProgressView progress;
    private final android.widget.ImageView next;
    private final PlayerIcon nextIcon = PlayerIcon.fill(PlayerIcon.NEXT,22);
    private final int slop;
    private float downX, downY, startX, startY;
    private boolean dragging;
    private boolean positioned;
    private MessageObject bound;
    private Boolean darkTheme;
    private int themeAccent, themeSurface, themeText, themeSecondary;
    private boolean paused;
    private boolean released;
    private boolean expanded;
    private final OnLayoutChangeListener boundsListener = (v,l,t,r,b,ol,ot,or,ob) -> confine();

    private SignatureMusicBubble(FrameLayout host) {
        super(host.getContext());
        this.host = host;
        slop = ViewConfiguration.get(getContext()).getScaledTouchSlop();
        pill = new MusicBlurSurface(this, AndroidUtilities.dp(32));
        setBackground(pill);
        art = new CoverImage(getContext(), 24);
        art.setRadius(AndroidUtilities.dp(26));
        art.setShowPlaceholderNote(false);
        FrameLayout.LayoutParams artParams = new FrameLayout.LayoutParams(AndroidUtilities.dp(52),AndroidUtilities.dp(52),Gravity.LEFT|Gravity.CENTER_VERTICAL);
        artParams.leftMargin=AndroidUtilities.dp(6);addView(art,artParams);
        progress = new MusicProgressView(getContext(),true);
        FrameLayout.LayoutParams ringParams = new FrameLayout.LayoutParams(AndroidUtilities.dp(60),AndroidUtilities.dp(60),Gravity.LEFT|Gravity.CENTER_VERTICAL);
        ringParams.leftMargin=AndroidUtilities.dp(2);addView(progress,ringParams);
        title = new TextView(getContext());
        title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        title.setSingleLine(true);
        title.setEllipsize(TextUtils.TruncateAt.END);
        title.setGravity(Gravity.CENTER_VERTICAL);
        FrameLayout.LayoutParams titleParams = new FrameLayout.LayoutParams(AndroidUtilities.dp(116), AndroidUtilities.dp(23), Gravity.LEFT | Gravity.TOP);
        titleParams.leftMargin = AndroidUtilities.dp(64);
        titleParams.topMargin = AndroidUtilities.dp(7);
        addView(title, titleParams);
        title.setOnClickListener(v -> openPlayer());
        title.setVisibility(GONE);
        artist = new TextView(getContext());
        artist.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        artist.setSingleLine(true);
        artist.setEllipsize(TextUtils.TruncateAt.END);
        FrameLayout.LayoutParams artistParams = new FrameLayout.LayoutParams(AndroidUtilities.dp(116), AndroidUtilities.dp(20), Gravity.LEFT | Gravity.TOP);
        artistParams.leftMargin = AndroidUtilities.dp(64);
        artistParams.topMargin = AndroidUtilities.dp(29);
        addView(artist, artistParams);
        artist.setOnClickListener(v -> openPlayer());
        artist.setVisibility(GONE);
        play = new RingPlayButton(getContext(), 0, 0, 18, 0, 0);
        play.setShowRing(false);
        GradientDrawable shade=new GradientDrawable();shade.setShape(GradientDrawable.OVAL);shade.setColor(0x66000000);
        play.setBackground(new android.graphics.drawable.InsetDrawable(shade,0,AndroidUtilities.dp(8),0,AndroidUtilities.dp(8)));
        FrameLayout.LayoutParams badge = new FrameLayout.LayoutParams(AndroidUtilities.dp(48), AndroidUtilities.dp(64), Gravity.LEFT | Gravity.TOP);
        badge.leftMargin = AndroidUtilities.dp(8);
        addView(play, badge);
        play.setOnClickListener(v -> {
            if (!expanded) { expandOrOpen(); return; }
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
        close.setVisibility(VISIBLE);
        setClickable(true);
        setFocusable(true);
        setContentDescription(LocaleController.getString(R.string.FlexyMusicExpand));
        setOnClickListener(v -> { if (expanded) openPlayer(); else expandOrOpen(); });
        art.setOnClickListener(v -> { if (expanded) openPlayer(); else expandOrOpen(); });
        next = new android.widget.ImageView(getContext());next.setImageDrawable(nextIcon);
        next.setScaleType(android.widget.ImageView.ScaleType.CENTER);
        next.setContentDescription(LocaleController.getString(R.string.Next));
        next.setOnClickListener(v -> MediaController.getInstance().playNextMessage());
        FrameLayout.LayoutParams nextParams = new FrameLayout.LayoutParams(AndroidUtilities.dp(48),-1,Gravity.RIGHT|Gravity.TOP);
        nextParams.rightMargin=AndroidUtilities.dp(48);addView(next,nextParams);next.setVisibility(GONE);
        play.setVisibility(VISIBLE);
        FrameLayout.LayoutParams closeParams=(FrameLayout.LayoutParams)close.getLayoutParams();closeParams.width=AndroidUtilities.dp(48);close.setLayoutParams(closeParams);
        setOnLongClickListener(v -> {
            PopupMenu menu = new PopupMenu(getContext(), this);
            menu.getMenu().add(LocaleController.getString(R.string.OEPlayerOpen)).setOnMenuItemClickListener(item -> { openPlayer(); return true; });
            menu.getMenu().add(LocaleController.getString(R.string.FlexyMusicCompact)).setOnMenuItemClickListener(item -> { setExpanded(!expanded); return true; });
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
                bubble.owner=new java.lang.ref.WeakReference<>(fragment);
                host.addOnLayoutChangeListener(bubble.boundsListener);
                return bubble;
            }
        }
        SignatureMusicBubble bubble = new SignatureMusicBubble(host);
        bubble.owner=new java.lang.ref.WeakReference<>(fragment);
        host.addView(bubble, new FrameLayout.LayoutParams(AndroidUtilities.dp(112), AndroidUtilities.dp(64), Gravity.TOP | Gravity.LEFT));
        return bubble;
    }

    private void expandOrOpen(){if(host.getWidth()>0&&host.getWidth()<AndroidUtilities.dp(232))openPlayer();else setExpanded(true);}

    private void openPlayer(){BaseFragment fragment=owner.get();if(!released&&fragment!=null)Md3Player.open(fragment,null);}

    public void release() {
        release(false);
    }
    public void releaseFromWindow() { release(true); }
    private void release(boolean windowDetaching) {
        if (released) return;
        released = true;
        owner.clear();
        host.removeOnLayoutChangeListener(boundsListener);
        cancelLongPress(); dragging = false; setPressed(false); setVisibility(GONE);
        host.requestDisallowInterceptTouchEvent(false);
        play.setPlaying(false, false);
        bound = null;
        art.setMessage(null); progress.setMessage(null);pill.detach();
        // The fragment root owns this inert child. attach() reuses it, keeping
        // dispatchDetachedFromWindow's children snapshot stable and bounded.
        if (!windowDetaching && getParent() == host) host.removeView(this);
    }

    public void update(boolean allowed, boolean dark) {
        if (released) return;
        MessageObject message = MediaController.getInstance().getPlayingMessageObject();
        boolean show = allowed && SignatureMusicPresentation.isCompact() && message != null && message.isMusic();
        setVisibility(show ? VISIBLE : GONE);
        if (show) pill.attach(); else pill.detach();
        if (!show) {
            play.setPlaying(false,false);
            if((message==null||!message.isMusic())&&bound!=null){bound=null;art.setMessage(null);play.setMessage(null);progress.setMessage(null);}
            return;
        }
        BaseFragment fragment=owner.get();
        Theme.ResourcesProvider provider=fragment!=null?fragment.getResourceProvider():null;
        int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, provider);
        int surface=Theme.getColor(Theme.key_windowBackgroundWhite,provider);
        int text=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider);
        int secondary=Theme.getColor(Theme.key_windowBackgroundWhiteGrayText,provider);
        if (darkTheme == null || darkTheme != dark || themeAccent != accent || themeSurface != surface || themeText != text || themeSecondary != secondary) {
            themeSurface=surface;themeText=text;themeSecondary=secondary;
            darkTheme = dark;
            themeAccent = accent;
            PlayerColors colors = PlayerColors.fromSignatureTheme(dark,provider);
            art.setColors(colors.primaryContainer, colors.onSurface);
            play.setColors(colors.primary, colors.surface, expanded ? colors.onSurface : android.graphics.Color.WHITE);
            pill.setColors(colors); progress.setColors(colors);nextIcon.setColor(colors.onSurface);
            title.setTextColor(colors.onSurface);
            artist.setTextColor(colors.onSurfaceVariant);
            close.setTextColor(colors.onSurface);
        }
        if (bound != message || !TextUtils.equals(title.getText(),message.getMusicTitle()) || !TextUtils.equals(artist.getText(),message.getMusicAuthor())) {
            bound = message;
            art.setMessage(message);
            title.setText(message.getMusicTitle());
            artist.setText(message.getMusicAuthor());
            play.setMessage(message);progress.setMessage(message);
            play.setPlaying(!MediaController.getInstance().isMessagePaused(), false);
        }
        progress.invalidate();
        boolean nowPaused = MediaController.getInstance().isMessagePaused();
        play.setContentDescription(LocaleController.getString(!expanded ? R.string.FlexyMusicExpand : nowPaused?R.string.AccActionPlay:R.string.AccActionPause));
        if (paused != nowPaused) { paused = nowPaused; play.setPlaying(!paused, false); }
        if (host.indexOfChild(this) != host.getChildCount() - 1) bringToFront();
        confine();
    }

    private void setExpanded(boolean value) {
        if (expanded == value) return;
        expanded = value;
        art.setShowPlaceholderNote(value);
        FrameLayout.LayoutParams params = (FrameLayout.LayoutParams) getLayoutParams();
        params.width = AndroidUtilities.dp(value ? 336 : 112);
        if (value && host.getWidth()>0) params.width=Math.min(params.width,Math.max(AndroidUtilities.dp(208),host.getWidth()-AndroidUtilities.dp(24)));
        setLayoutParams(params);
        boolean labels=value && params.width>=AndroidUtilities.dp(288) && getResources().getConfiguration().fontScale<=1.5f;
        title.setVisibility(labels ? VISIBLE : GONE);artist.setVisibility(labels ? VISIBLE : GONE);
        for (TextView text : new TextView[]{title,artist}) {
            FrameLayout.LayoutParams lp=(FrameLayout.LayoutParams)text.getLayoutParams();
            lp.leftMargin=AndroidUtilities.dp(68);lp.width=Math.max(0,params.width-AndroidUtilities.dp(216));text.setLayoutParams(lp);
        }
        close.setVisibility(VISIBLE);next.setVisibility(value ? VISIBLE : GONE);play.setVisibility(VISIBLE);
        FrameLayout.LayoutParams badge=(FrameLayout.LayoutParams)play.getLayoutParams();
        badge.width=AndroidUtilities.dp(48);badge.height=AndroidUtilities.dp(64);badge.rightMargin=AndroidUtilities.dp(value ? 96 : 0);badge.leftMargin=AndroidUtilities.dp(value ? 0 : 8);
        badge.gravity=(value ? Gravity.RIGHT : Gravity.LEFT)|Gravity.TOP;play.setLayoutParams(badge);
        BaseFragment fragment=owner.get();PlayerColors colors=PlayerColors.fromSignatureTheme(darkTheme!=null&&darkTheme,fragment==null?null:fragment.getResourceProvider());
        play.setColors(colors.primary,colors.surface,value?colors.onSurface:android.graphics.Color.WHITE);
        if(value)play.setBackground(null);
        else { GradientDrawable shade=new GradientDrawable();shade.setShape(GradientDrawable.OVAL);shade.setColor(0x66000000);play.setBackground(new android.graphics.drawable.InsetDrawable(shade,0,AndroidUtilities.dp(8),0,AndroidUtilities.dp(8))); }
        setContentDescription(LocaleController.getString(value ? R.string.OEPlayerOpen : R.string.FlexyMusicExpand));
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
        if (expanded && host.getWidth()<AndroidUtilities.dp(232)) { setExpanded(false); return; }
        if (expanded) {
            int desired=Math.min(AndroidUtilities.dp(336),Math.max(AndroidUtilities.dp(208),host.getWidth()-AndroidUtilities.dp(24)));
            if(getLayoutParams().width!=desired){expanded=false;setExpanded(true);return;}
        }
        float x = positioned ? getX() : host.getWidth() - AndroidUtilities.dp(68);
        float y = positioned ? getY() : host.getHeight() * .45f;
        setX(SignatureMusicStyle.clamp(x, side, host.getWidth() - getLayoutParams().width - side));
        setY(SignatureMusicStyle.clamp(y, Math.min(top, Math.max(0, host.getHeight() - getLayoutParams().height)),
                host.getHeight() - getLayoutParams().height - bottom));
        positioned = true;
    }

    @Override public void draw(android.graphics.Canvas canvas) { if (!MusicBlurSurface.isCapturing()) super.draw(canvas); }

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
