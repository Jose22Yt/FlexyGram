package app.exteraless.player;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.MessageObject;

/** Passive progress decoration: updated by existing playback notifications, no animator or timer. */
final class MusicProgressView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private MessageObject message;
    private int accent, track;
    private final boolean circular;
    MusicProgressView(Context context, boolean circular) {
        super(context); this.circular = circular;
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO); setClickable(false);
    }
    void setMessage(MessageObject value) { message = value; invalidate(); }
    void setColors(PlayerColors colors) { accent = colors.primary; track = colors.outlineVariant; invalidate(); }
    @Override protected void onDraw(Canvas canvas) {
        float progress = message == null ? 0 : Math.max(0, Math.min(1, message.audioProgress));
        paint.setStrokeWidth(AndroidUtilities.dpf2(2)); paint.setStrokeCap(Paint.Cap.ROUND);
        if (circular) {
            paint.setStyle(Paint.Style.STROKE); paint.setColor(track);
            float inset=AndroidUtilities.dpf2(2);
            canvas.drawArc(inset,inset,getWidth()-inset,getHeight()-inset,-90,360,false,paint);
            paint.setColor(accent);canvas.drawArc(inset,inset,getWidth()-inset,getHeight()-inset,-90,360*progress,false,paint);
        } else {
            paint.setStyle(Paint.Style.FILL);paint.setColor(track);canvas.drawRect(0,0,getWidth(),getHeight(),paint);
            paint.setColor(accent);float filled=getWidth()*progress;
            canvas.drawRect(getLayoutDirection()==LAYOUT_DIRECTION_RTL?getWidth()-filled:0,0,
                    getLayoutDirection()==LAYOUT_DIRECTION_RTL?getWidth():filled,getHeight(),paint);
        }
    }
}
