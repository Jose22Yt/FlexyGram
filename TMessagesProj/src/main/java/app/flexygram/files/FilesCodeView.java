/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;
import android.content.Context;
import android.graphics.*;
import android.text.Layout;
import android.view.Gravity;
import android.widget.EditText;
import org.telegram.messenger.AndroidUtilities;
/** Native editable text. Visible visual-line gutter uses a reusable char buffer, no per-frame strings. */
final class FilesCodeView extends EditText {
    private final Paint gutter=new Paint(Paint.ANTI_ALIAS_FLAG);private final char[] digits=new char[12];
    FilesCodeView(Context c,int textColor,int hintColor){super(c);setTextSize(15);setTypeface(Typeface.MONOSPACE);setTextColor(textColor);setHintTextColor(hintColor);gutter.setColor(hintColor);gutter.setTextSize(getTextSize()*.8f);setGravity(Gravity.TOP|Gravity.START);setPadding(AndroidUtilities.dp(56),AndroidUtilities.dp(12),AndroidUtilities.dp(12),AndroidUtilities.dp(16));setHorizontallyScrolling(true);setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE|android.text.InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);setTypeface(Typeface.MONOSPACE);setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(app.flexygram.files.core.SelectedDocument.MAX_TEXT)});}
    @Override protected void onDraw(Canvas canvas){super.onDraw(canvas);Layout layout=getLayout();if(layout==null)return;int top=getScrollY(),bottom=top+getHeight();int first=layout.getLineForVertical(Math.max(0,top-getTotalPaddingTop())),last=layout.getLineForVertical(bottom);for(int line=first;line<=last;line++){int n=line+1,end=digits.length,start=end;do{digits[--start]=(char)('0'+n%10);n/=10;}while(n>0);canvas.drawText(digits,start,end-start,getScrollX()+AndroidUtilities.dp(6),getTotalPaddingTop()+layout.getLineBaseline(line),gutter);}}
}
