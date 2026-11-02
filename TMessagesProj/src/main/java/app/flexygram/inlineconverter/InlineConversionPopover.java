/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;

import android.app.DatePickerDialog;
import android.content.Context;
import android.graphics.Rect;
import android.graphics.drawable.GradientDrawable;
import android.view.*;
import android.widget.*;
import androidx.recyclerview.widget.RecyclerView;
import java.math.BigDecimal;
import java.text.NumberFormat;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** A window-local, themed, bounded popover. No overlays, blur, bitmaps or animation loop. */
public final class InlineConversionPopover {
    private final View anchor;
    private final Theme.ResourcesProvider theme;
    private final Locale locale;
    private PopupWindow window;
    private ViewTreeObserver observer;
    private DatePickerDialog datePicker;
    private final ViewTreeObserver.OnScrollChangedListener scroll=this::dismiss;
    private final ViewTreeObserver.OnGlobalLayoutListener layout=this::dismiss;
    private final View.OnAttachStateChangeListener attach=new View.OnAttachStateChangeListener(){
        @Override public void onViewAttachedToWindow(View v){}
        @Override public void onViewDetachedFromWindow(View v){dismiss();}
    };
    public InlineConversionPopover(View anchor,Theme.ResourcesProvider theme){this.anchor=anchor;this.theme=theme;Locale region=LocaleController.getInstance().getCurrentLocale();locale=region==null?Locale.getDefault():region;}
    private String text(int resource){return LocaleController.getString(resource);}
    private int color(int key){return Theme.getColor(key,theme);}
    private TextView label(Context context,String value,int size,boolean secondary){
        TextView view=new TextView(context);view.setText(value);view.setTextSize(size);view.setTextColor(color(secondary?Theme.key_dialogTextGray:Theme.key_dialogTextBlack));view.setPadding(0,AndroidUtilities.dp(4),0,AndroidUtilities.dp(4));view.setTextDirection(View.TEXT_DIRECTION_LOCALE);return view;
    }
    private TextView button(Context context,String value,Runnable action){
        TextView view=label(context,value,15,false);view.setTextColor(color(Theme.key_dialogTextBlue));view.setMinHeight(AndroidUtilities.dp(48));view.setGravity(Gravity.CENTER_VERTICAL);view.setBackground(Theme.createSelectorDrawable(color(Theme.key_listSelector),2));view.setOnClickListener(v->action.run());view.setFocusable(true);return view;
    }
    public void show(InlineConversionMatch match,int messageDate,float localX,float localY){
        show(match,messageDate,localX,localY,null,null,-1);
    }
    private void show(InlineConversionMatch match,int messageDate,float localX,float localY,ZoneId selected,LocalDate selectedDate,int offsetIndex){
        dismiss();if(!anchor.isAttachedToWindow())return;
        Context context=anchor.getContext();InlineConversionConfig.Snapshot config=InlineConversionConfig.get();
        if(!config.accepts(match))return;
        LinearLayout content=new LinearLayout(context);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(AndroidUtilities.dp(16),AndroidUtilities.dp(10),AndroidUtilities.dp(16),AndroidUtilities.dp(8));
        GradientDrawable surface=new GradientDrawable();surface.setColor(color(Theme.key_dialogBackground));surface.setCornerRadius(AndroidUtilities.dp(18));content.setBackground(surface);
        content.addView(label(context,match.raw,14,true));String result=null;
        if(match.type==InlineConversionMatch.Type.CURRENCY){
            content.addView(label(context,match.code+" → "+config.targetCurrency,19,false));
            content.addView(label(context,text(R.string.InlineConversionCurrencyUnavailable),14,true));
        }else if(match.type==InlineConversionMatch.Type.UNIT){
            UnitConversionEngine.Result converted=UnitConversionEngine.convert(match.value,match.code,config.imperial(locale));
            NumberFormat format=NumberFormat.getNumberInstance(locale);format.setMaximumFractionDigits(2);
            String formatted=format.format(converted.value);boolean rounded=converted.value.stripTrailingZeros().scale()>2;
            result=(rounded?"≈ ":"")+formatted+" "+converted.unit;
            content.addView(label(context,result,22,false));
            content.addView(label(context,text(R.string.InlineConversionOffline),13,true));
        }else {
            List<ZoneId> sources;
            try{sources=TimeConversionEngine.sourceZones(match.code);}catch(DateTimeException invalid){sources=Collections.emptyList();}
            if(sources.isEmpty())content.addView(label(context,text(R.string.InlineConversionUnknownZone),15,false));
            else {
                ZoneId source=selected!=null?selected:sources.size()==1?sources.get(0):null;
                if(source==null){
                    content.addView(label(context,text(R.string.InlineConversionAmbiguousZone),15,false));
                    for(ZoneId zone:sources)content.addView(button(context,zone.getId(),()->show(match,messageDate,localX,localY,zone,null,-1)));
                }else{
                    ZoneId target=config.zone();LocalDate date=selectedDate==null?TimeConversionEngine.messageDate(messageDate,source):selectedDate;
                    content.addView(label(context,source.getId()+" → "+target.getId(),13,true));
                    content.addView(label(context,text(selectedDate==null?R.string.InlineConversionDateAssumption:R.string.InlineConversionSelectedDate)+" "+date,13,true));
                    content.addView(button(context,text(R.string.InlineConversionChangeDate),()->{
                        datePicker=new DatePickerDialog(context,(view,year,month,day)->{datePicker=null;show(match,messageDate,localX,localY,source,LocalDate.of(year,month+1,day),-1);},date.getYear(),date.getMonthValue()-1,date.getDayOfMonth());
                        datePicker.show();
                    }));
                    List<ZonedDateTime> values=TimeConversionEngine.convert(match.hour,match.minute,date,source,target);
                    if(values.isEmpty())content.addView(label(context,text(R.string.InlineConversionTimeGap),15,false));
                    else if(values.size()>1&&offsetIndex<0){
                        content.addView(label(context,text(R.string.InlineConversionTimeOverlap),15,false));
                        for(int i=0;i<values.size();i++){final int choice=i;String offset=values.get(i).withZoneSameInstant(source).getOffset().toString();content.addView(button(context,"UTC "+offset,()->show(match,messageDate,localX,localY,source,date,choice)));}
                    }else{
                        ZonedDateTime converted=values.get(Math.max(0,offsetIndex));
                        result=converted.format(DateTimeFormatter.ofPattern("uuuu-MM-dd HH:mm xxx",locale))+" · "+target.getId();
                        content.addView(label(context,result,20,false));
                    }
                }
            }
        }
        LinearLayout actions=new LinearLayout(context);actions.setOrientation(LinearLayout.HORIZONTAL);
        if(result!=null){String copy=result;actions.addView(button(context,text(R.string.InlineConversionCopy),()->{AndroidUtilities.addToClipboard(copy);dismiss();}),new LinearLayout.LayoutParams(0,-2,1));}
        actions.addView(button(context,text(R.string.InlineConversionClose),this::dismiss),new LinearLayout.LayoutParams(0,-2,1));content.addView(actions);
        Rect available=viewport();int width=Math.min(AndroidUtilities.dp(320),available.width()-AndroidUtilities.dp(12));
        if(width<AndroidUtilities.dp(160)||available.height()<AndroidUtilities.dp(96))return;
        ScrollView container=new ScrollView(context);container.setFillViewport(false);container.addView(content);
        container.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(available.height()-AndroidUtilities.dp(12),View.MeasureSpec.AT_MOST));
        int height=container.getMeasuredHeight();int[] location=new int[2];anchor.getLocationOnScreen(location);
        int x=Math.max(available.left+AndroidUtilities.dp(6),Math.min(location[0]+(int)localX-width/2,available.right-width-AndroidUtilities.dp(6)));
        int y=location[1]+(int)localY-height-AndroidUtilities.dp(10);
        if(y<available.top)y=location[1]+(int)localY+AndroidUtilities.dp(12);
        y=Math.max(available.top+AndroidUtilities.dp(6),Math.min(y,available.bottom-height-AndroidUtilities.dp(6)));
        window=new PopupWindow(container,width,height,true);window.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(android.graphics.Color.TRANSPARENT));window.setOutsideTouchable(true);window.setClippingEnabled(true);window.setInputMethodMode(PopupWindow.INPUT_METHOD_NOT_NEEDED);window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING);
        window.setOnDismissListener(()->{window=null;removeListeners();if(datePicker!=null){datePicker.dismiss();datePicker=null;}});
        try{
            // showAtLocation uses window coordinates; viewport/anchor above use screen coordinates.
            int[] rootScreen=new int[2],rootWindow=new int[2];anchor.getRootView().getLocationOnScreen(rootScreen);anchor.getRootView().getLocationInWindow(rootWindow);
            window.showAtLocation(anchor,Gravity.TOP|Gravity.LEFT,x-rootScreen[0]+rootWindow[0],y-rootScreen[1]+rootWindow[1]);
            observer=anchor.getRootView().getViewTreeObserver();observer.addOnScrollChangedListener(scroll);observer.addOnGlobalLayoutListener(layout);anchor.addOnAttachStateChangeListener(attach);
        }catch(WindowManager.BadTokenException gone){dismiss();}
    }
    private Rect viewport(){
        Rect visible=new Rect();anchor.getWindowVisibleDisplayFrame(visible);
        ViewParent parent=anchor.getParent();
        while(parent instanceof View){
            if(parent instanceof RecyclerView){View list=(View)parent;Rect local=new Rect();int[] position=new int[2];list.getLocationOnScreen(position);
                if(list.getLocalVisibleRect(local)){local.offset(position[0],position[1]);local.top+=list.getPaddingTop();local.bottom-=list.getPaddingBottom();visible.intersect(local);}break;}
            parent=parent.getParent();
        }
        // Keep clear of overlay action/pinned bars and composer even with clipToPadding=false.
        visible.top+=AndroidUtilities.dp(56);visible.bottom-=AndroidUtilities.dp(72);
        return visible;
    }
    private void removeListeners(){if(observer!=null&&observer.isAlive()){observer.removeOnScrollChangedListener(scroll);observer.removeOnGlobalLayoutListener(layout);}observer=null;anchor.removeOnAttachStateChangeListener(attach);}
    public void dismiss(){PopupWindow previous=window;window=null;if(previous!=null)previous.dismiss();removeListeners();if(datePicker!=null){datePicker.dismiss();datePicker=null;}}
}
