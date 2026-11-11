/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

import static org.telegram.messenger.AndroidUtilities.dp;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Path;
import android.graphics.Paint;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.graphics.RectF;
import android.os.Build;
import android.text.TextUtils;
import android.view.Choreographer;
import android.view.DisplayCutout;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ImageLocation;
import org.telegram.messenger.NotchInfoUtils;
import org.telegram.messenger.SharedConfig;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.AvatarDrawable;
import org.telegram.ui.Components.BackupImageView;

/** Only the capsule is attached to decor: no full-screen touch-consuming overlay. */
final class CameraPopCapsule extends LinearLayout {
    private final BackupImageView avatar;
    private final TextView name, detail;
    private final FrameLayout root;
    private final View.OnLayoutChangeListener layoutListener;
    private final int[] location = new int[2];
    private final Runnable reposition=this::position;
    private Choreographer.FrameCallback frame;
    private Runnable completed;
    private float destinationX, destinationY;
    private float terminalX=.01f,terminalY=.01f,surfaceNeck;
    private boolean closing,hasCutout;
    private final CameraPopMotion motionValue=new CameraPopMotion();
    private final Path surfacePath=new Path();
    private final Paint surfacePaint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint borderPaint=new Paint(Paint.ANTI_ALIAS_FLAG);

    CameraPopCapsule(FrameLayout root) {
        super(root.getContext());
        this.root=root;
        Context context=getContext();
        setOrientation(HORIZONTAL); setGravity(Gravity.CENTER_VERTICAL);
        setPadding(dp(14),dp(12),dp(14),dp(12));
        setMinimumHeight(dp(76)); setClickable(true); setFocusable(true);
        setWillNotDraw(false);borderPaint.setStyle(Paint.Style.STROKE);borderPaint.setStrokeWidth(dp(1));
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
        setAccessibilityLiveRegion(ACCESSIBILITY_LIVE_REGION_POLITE);
        avatar=new BackupImageView(context); avatar.setRoundRadius(dp(23));
        addView(avatar,new LinearLayout.LayoutParams(dp(46),dp(46)));
        LinearLayout text=new LinearLayout(context); text.setOrientation(VERTICAL);
        LinearLayout.LayoutParams textParams=new LinearLayout.LayoutParams(0,LayoutParams.WRAP_CONTENT,1f);
        textParams.setMarginStart(dp(12)); addView(text,textParams);
        name=new TextView(context); name.setTextSize(15); name.setTypeface(AndroidUtilities.bold());
        name.setSingleLine(true); name.setEllipsize(TextUtils.TruncateAt.END);
        detail=new TextView(context); detail.setTextSize(13); detail.setMaxLines(2);
        detail.setEllipsize(TextUtils.TruncateAt.END);
        text.addView(name,new LinearLayout.LayoutParams(LayoutParams.MATCH_PARENT,LayoutParams.WRAP_CONTENT));
        text.addView(detail,new LinearLayout.LayoutParams(LayoutParams.MATCH_PARENT,LayoutParams.WRAP_CONTENT));
        layoutListener=(v,l,t,r,b,ol,ot,or,ob)->{
            if(frame!=null && (r-l!=or-ol || b-t!=ob-ot)) {
                boolean exiting=closing;Runnable done=completed;cancelMotion();
                position();apply(exiting?0f:1f);if(done!=null)done.run();
            } else if(frame==null && !closing) position();
        };
        root.addOnLayoutChangeListener(layoutListener);
        setOnApplyWindowInsetsListener((v,insets)->{removeCallbacks(reposition);post(reposition);return insets;});
        updateColors();
    }

    void bind(String title, String description, Object peer) {
        updateColors(); name.setText(title); detail.setText(description);
        setContentDescription(title+". "+description);
        AvatarDrawable placeholder=new AvatarDrawable();
        if (peer instanceof TLRPC.User) {
            TLRPC.User user=(TLRPC.User)peer; placeholder.setInfo(user);
            avatar.setImage(ImageLocation.getForUser(user,ImageLocation.TYPE_SMALL),"46_46",placeholder,user);
        } else if (peer instanceof TLRPC.Chat) {
            TLRPC.Chat chat=(TLRPC.Chat)peer; placeholder.setInfo(chat);
            avatar.setImage(ImageLocation.getForChat(chat,ImageLocation.TYPE_SMALL),"46_46",placeholder,chat);
        } else {
            // Clearing an earlier peer request is essential when privacy is enabled.
            placeholder.setInfo(0,"F","G"); avatar.setImageDrawable(placeholder);
        }
    }

    private void updateColors() {
        surfacePaint.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        borderPaint.setColor(Theme.getColor(Theme.key_divider));
        name.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        detail.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
        invalidate();
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float w=getWidth(),h=getHeight(),neck=h*surfaceNeck,cx=w/2f;
        float radius=Math.min(dp(28),Math.min(w/2f,(h-neck)/2f)),shoulder=Math.min(neck*1.5f,w/2f-radius);
        surfacePath.rewind();surfacePath.moveTo(cx,0);
        surfacePath.cubicTo(cx+neck*.55f,0,cx+neck*.8f,neck,cx+shoulder,neck);
        surfacePath.lineTo(w-radius,neck);surfacePath.quadTo(w,neck,w,neck+radius);
        surfacePath.lineTo(w,h-radius);surfacePath.quadTo(w,h,w-radius,h);
        surfacePath.lineTo(radius,h);surfacePath.quadTo(0,h,0,h-radius);
        surfacePath.lineTo(0,neck+radius);surfacePath.quadTo(0,neck,radius,neck);
        surfacePath.lineTo(cx-shoulder,neck);
        surfacePath.cubicTo(cx-neck*.8f,neck,cx-neck*.55f,0,cx,0);surfacePath.close();
        canvas.drawPath(surfacePath,surfacePaint);canvas.drawPath(surfacePath,borderPaint);
    }
    @Override protected void dispatchDraw(Canvas canvas) {
        int save=canvas.save();canvas.clipPath(surfacePath);super.dispatchDraw(canvas);canvas.restoreToCount(save);
    }

    void position() {
        int width=root.getWidth(), height=root.getHeight();
        if(width<=0 || height<=0) return;
        int left=0,top=AndroidUtilities.statusBarHeight,right=0,bottom=0;
        RectF notch=new RectF();
        WindowInsets insets=root.getRootWindowInsets();
        if(insets!=null) {
            if(Build.VERSION.SDK_INT>=30) {
                android.graphics.Insets safe=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
                left=safe.left;top=safe.top;right=safe.right;bottom=safe.bottom;
            } else {
                left=insets.getSystemWindowInsetLeft();top=insets.getSystemWindowInsetTop();
                right=insets.getSystemWindowInsetRight();bottom=insets.getSystemWindowInsetBottom();
            }
            if(Build.VERSION.SDK_INT>=28) {
                DisplayCutout cutout=insets.getDisplayCutout();
                if(cutout!=null) {
                    root.getLocationInWindow(location);
                    // WindowInsets cutout rectangles have already been inset to this window.
                    for(Rect rect:cutout.getBoundingRects()) {
                        RectF candidate=new RectF(rect); candidate.offset(-location[0],-location[1]);
                        if(candidate.top<height/2f && (notch.isEmpty() || candidate.top<notch.top)) notch.set(candidate);
                    }
                    if(Build.VERSION.SDK_INT>=31) {
                        Path path=cutout.getCutoutPath();
                        if(path!=null) {
                            // Use the actual contour when available, rather than its padded safe bounds.
                            // Unlike the bounds above, this path is in display coordinates.
                            Path local=new Path(path);root.getLocationOnScreen(location);
                            local.offset(-location[0],-location[1]);
                            if(!notch.isEmpty()) {
                                Path region=new Path();region.addRect(notch,Path.Direction.CW);
                                if(!local.op(region,Path.Op.INTERSECT))local.reset();
                            }
                            RectF precise=new RectF();local.computeBounds(precise,true);
                            if(!precise.isEmpty())notch.set(precise);
                        }
                    }
                }
            }
        }
        if(notch.isEmpty() && width>=height) {
            // Do not interpret portrait firmware paths in landscape.
            notch.setEmpty();
        } else if(notch.isEmpty()) {
            // Existing Telegram detector: best-effort only; never a dependency.
            try {
                NotchInfoUtils.NotchInfo info=NotchInfoUtils.getInfo(getContext());
                if(info!=null) {
                    notch.set(info.bounds); root.getLocationOnScreen(location);
                    notch.offset(-location[0],-location[1]);
                }
            } catch(RuntimeException ignored) { /* Some OEMs do not expose this resource. */ }
        }
        int available=Math.max(1,Math.min(dp(360),width-left-right-dp(24)));
        measure(MeasureSpec.makeMeasureSpec(available,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        int cardHeight=getMeasuredHeight();
        CameraPopGeometry.Placement p=CameraPopGeometry.place(width,height,left,top,right,bottom,
                dp(360),cardHeight,dp(12),dp(6),notch.left,notch.top,notch.right,notch.bottom);
        FrameLayout.LayoutParams params=(FrameLayout.LayoutParams)getLayoutParams();
        if(params.width!=p.width || params.leftMargin!=Math.round(p.x) || params.topMargin!=Math.round(p.y)) {
            params.width=p.width;params.leftMargin=Math.round(p.x);params.topMargin=Math.round(p.y);setLayoutParams(params);
        }
        destinationX=p.originX-(p.x+p.width/2f);
        destinationY=p.originY-(p.y+cardHeight/2f);
        hasCutout=p.cutout;
        float terminal=hasCutout?Math.max(1f,Math.min(notch.width(),notch.height())*.60f):1f;
        terminalX=Math.min(1f,terminal/p.width);terminalY=Math.min(1f,terminal/Math.max(1,cardHeight));
    }

    private boolean reducedMotion() {
        return !SharedConfig.animationsEnabled() || AndroidUtilities.isAccessibilityScreenReaderEnabled()
                || (Build.VERSION.SDK_INT>=26 && !ValueAnimator.areAnimatorsEnabled());
    }
    void enter() { position(); motion(false,null); }
    void exit(Runnable completion) { position(); motion(true,completion); }
    private void motion(boolean exit,Runnable completion) {
        cancelMotion(); closing=exit; completed=completion;
        if(reducedMotion()) { apply(exit?0f:1f);finish();return; }
        final long[] start={0};
        final long duration=(exit?280L:300L)*1_000_000L;
        // Own finite clock: Android's x5/x10 animation duration does not slow the app.
        apply(exit?1f:0f);
        frame=time->{
            if(start[0]==0) start[0]=time;
            float fraction=Math.min(1f,(float)(time-start[0])/duration);
            float eased=exit?1f-(float)Math.pow(1f-fraction,2.2):1f-(float)Math.pow(1f-fraction,3);
            apply(exit?1f-eased:eased);
            if(fraction<1f) Choreographer.getInstance().postFrameCallback(frame);
            else {frame=null;finish();}
        };
        Choreographer.getInstance().postFrameCallback(frame);
    }
    private void apply(float progress) {
        motionValue.update(progress,closing,terminalX,terminalY,destinationX,destinationY,hasCutout);
        setScaleX(motionValue.scaleX);setScaleY(motionValue.scaleY);
        setTranslationX(motionValue.x);setTranslationY(motionValue.y);setAlpha(motionValue.alpha);
        avatar.setAlpha(motionValue.contentAlpha);name.setAlpha(motionValue.contentAlpha);detail.setAlpha(motionValue.contentAlpha);
        surfaceNeck=motionValue.neck;invalidate();
    }
    private void finish() {Runnable done=completed;completed=null;if(done!=null)done.run();}
    void cancelMotion() {
        if(frame!=null) Choreographer.getInstance().removeFrameCallback(frame);
        frame=null;completed=null;
    }
    void release() {
        cancelMotion(); removeCallbacks(reposition);
        root.removeOnLayoutChangeListener(layoutListener);
        setOnApplyWindowInsetsListener(null);setOnClickListener(null);
        avatar.setImageDrawable(null);root.removeView(this);
    }
}
