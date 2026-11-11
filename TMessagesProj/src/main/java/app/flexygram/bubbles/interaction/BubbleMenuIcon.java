package app.flexygram.bubbles.interaction;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.drawable.Drawable;
import app.flexygram.bubbles.interaction.BubbleActionPanelView.Action;

/** Official iOS glyphs; legacy optional-pack geometry is retained as a fallback. */
public final class BubbleMenuIcon extends Drawable {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path path = new Path();
    private final Action action;
    private final Drawable original;
    public BubbleMenuIcon(Action action, int color) {
        this.action = action;
        original = app.flexygram.icons.ExactIcons.direct(originalAsset(action));
        if (original != null) original.setTint(color);
        paint.setColor(color); paint.setStyle(Paint.Style.STROKE);
        if (original != null) return;
        paint.setStrokeWidth(1.75f); paint.setStrokeCap(Paint.Cap.ROUND); paint.setStrokeJoin(Paint.Join.ROUND);
        switch (action) {
            case REPLY: case FORWARD:
                path.moveTo(9,5);path.lineTo(4,10);path.lineTo(9,15);
                path.moveTo(4,10);path.lineTo(13,10);path.cubicTo(18,10,20,13,20,19);break;
            case STICKER:
                path.moveTo(21,13);path.lineTo(13,21);path.cubicTo(5,22,1,17,3,10);path.cubicTo(5,1,18,1,21,9);path.close();
                path.moveTo(13,21);path.lineTo(14,15);path.lineTo(21,13);
                path.moveTo(8,14);path.quadTo(11,17,14,13);break;
            case PIN:
                path.moveTo(14,3);path.lineTo(21,10);path.lineTo(18,12);path.lineTo(16,17);path.lineTo(7,8);path.lineTo(12,6);path.close();
                path.moveTo(11,13);path.lineTo(4,21);break;
            case DELETE:
                path.moveTo(4,6);path.lineTo(20,6);path.moveTo(9,6);path.lineTo(9,3);path.lineTo(15,3);path.lineTo(15,6);
                path.moveTo(6,9);path.lineTo(7,21);path.lineTo(17,21);path.lineTo(18,9);break;
            case EDIT:
                path.moveTo(4,20);path.lineTo(5,14);path.lineTo(16,3);path.lineTo(21,8);path.lineTo(10,19);path.close();path.moveTo(13,6);path.lineTo(18,11);break;
            case SELECT:
                path.moveTo(7,12);path.lineTo(10,15);path.lineTo(17,8);break;
            case SAVE:
                path.moveTo(12,3);path.lineTo(12,16);path.moveTo(7,11);path.lineTo(12,16);path.lineTo(17,11);
                path.moveTo(4,17);path.lineTo(4,21);path.lineTo(20,21);path.lineTo(20,17);break;
            case SHARE:
                path.moveTo(12,15);path.lineTo(12,2);path.moveTo(7,7);path.lineTo(12,2);path.lineTo(17,7);
                path.moveTo(7,10);path.lineTo(4,10);path.lineTo(4,22);path.lineTo(20,22);path.lineTo(20,10);path.lineTo(17,10);break;
            case LINK:
                path.moveTo(9,8);path.lineTo(7,8);path.cubicTo(0,8,0,17,7,17);path.lineTo(10,17);
                path.moveTo(15,8);path.lineTo(17,8);path.cubicTo(24,8,24,17,17,17);path.lineTo(14,17);
                path.moveTo(8,12.5f);path.lineTo(16,12.5f);break;
        }
    }
    private static int originalAsset(Action action) {
        switch (action) {
            case REPLY: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_reply;
            case FORWARD: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_forward;
            case COPY: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_copy;
            case STICKER: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_sticker;
            case PIN: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_pin;
            case DELETE: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_delete;
            case EDIT: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_edit;
            case SELECT: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_select;
            case SAVE: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_download;
            case SHARE: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_share;
            case LINK: return org.telegram.messenger.R.drawable.fg_ios_original_chat_context_menu_link;
            default: return app.flexygram.icons.IosOriginalAssets.MORE;
        }
    }
    @Override public void draw(Canvas canvas) {
        if (original != null) { original.setBounds(getBounds()); original.draw(canvas); return; }
        int save = canvas.save();canvas.translate(getBounds().left,getBounds().top);canvas.scale(getBounds().width()/24f,getBounds().height()/24f);
        if(action==Action.FORWARD){canvas.translate(24,0);canvas.scale(-1,1);}
        canvas.drawPath(path,paint);
        if(action==Action.COPY){canvas.drawRoundRect(8,6,20,22,2,2,paint);canvas.drawRoundRect(4,2,16,18,2,2,paint);}
        if(action==Action.SELECT)canvas.drawRoundRect(3,3,21,21,4,4,paint);
        if(action==Action.STICKER){canvas.drawPoint(8,9,paint);canvas.drawPoint(14,9,paint);}
        if(action==Action.MORE){canvas.drawCircle(5,12,.85f,paint);canvas.drawCircle(12,12,.85f,paint);canvas.drawCircle(19,12,.85f,paint);}
        canvas.restoreToCount(save);
    }
    @Override public void setAlpha(int alpha){paint.setAlpha(alpha);if(original!=null)original.setAlpha(alpha);invalidateSelf();}
    @Override public void setColorFilter(ColorFilter filter){paint.setColorFilter(filter);if(original!=null)original.setColorFilter(filter);invalidateSelf();}
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
}
