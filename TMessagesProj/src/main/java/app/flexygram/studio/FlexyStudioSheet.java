/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.view.*;
import android.widget.*;
import app.flexygram.studio.core.StudioCodec;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.*;
import org.telegram.ui.Components.BulletinFactory;
import java.lang.ref.WeakReference;

/** Native bottom sheet: real validated sections only; no fixed-height decorative panel or blur. */
public final class FlexyStudioSheet extends BottomSheet {
    private final WeakReference<BaseFragment> owner;
    private boolean busy;
    private final TextView apply;
    private final Theme.ResourcesProvider provider;
    public FlexyStudioSheet(BaseFragment fragment,StudioCodec.Preset preset,String filename,int bytes) {
        super(fragment.getParentActivity(),false,fragment.getResourceProvider());
        owner=new WeakReference<>(fragment);provider=fragment.getResourceProvider();Context c=getContext();
        setBackgroundColor(color(Theme.key_windowBackgroundGray));setApplyTopPadding(false);
        LinearLayout all=new LinearLayout(c);all.setOrientation(LinearLayout.VERTICAL);all.setPadding(dp(20),dp(18),dp(20),dp(12));
        TextView title=text(getString(R.string.FlexyStudioApplyTitle),22,Theme.key_windowBackgroundWhiteBlackText);
        title.setTypeface(AndroidUtilities.bold());add(all,title,0,12);
        LinearLayout info=panel(c);info.setOrientation(LinearLayout.HORIZONTAL);
        ImageView icon=new ImageView(c);icon.setImageResource(R.drawable.flexy_studio_document);icon.setColorFilter(color(Theme.key_windowBackgroundWhiteBlueText));
        icon.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        LinearLayout.LayoutParams image=new LinearLayout.LayoutParams(dp(48),dp(64));image.gravity=Gravity.CENTER_VERTICAL;info.addView(icon,image);
        LinearLayout detail=new LinearLayout(c);detail.setOrientation(LinearLayout.VERTICAL);detail.setPaddingRelative(dp(14),0,0,0);
        TextView name=text(filename,17,Theme.key_windowBackgroundWhiteBlackText);name.setMaxLines(3);name.setEllipsize(android.text.TextUtils.TruncateAt.END);
        detail.addView(name);detail.addView(text(getString(R.string.FlexyStudioFileDescription),14,Theme.key_windowBackgroundWhiteGrayText2));
        detail.addView(text(AndroidUtilities.formatFileSize(bytes),14,Theme.key_windowBackgroundWhiteGrayText2));
        detail.addView(text(getString(R.string.FlexyStudioCompatible),14,Theme.key_windowBackgroundWhiteBlueText));
        info.addView(detail,new LinearLayout.LayoutParams(0,-2,1));add(all,info,0,14);
        add(all,text(getString(R.string.FlexyStudioIncludes),14,Theme.key_windowBackgroundWhiteBlueText),0,8);
        LinearLayout sections=panel(c);sections.setPadding(0,0,0,0);sections.setOrientation(LinearLayout.VERTICAL);
        for(String id:preset.sections.keySet()) {
            LinearLayout row=new LinearLayout(c);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(16),dp(12),dp(16),dp(12));row.setMinimumHeight(dp(52));
            ImageView line=new ImageView(c);line.setImageResource(FlexyStudioText.icon(id));line.setColorFilter(color(Theme.key_windowBackgroundWhiteBlackText));line.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            row.addView(line,new LinearLayout.LayoutParams(dp(24),dp(24)));
            TextView label=text(getString(FlexyStudioText.section(id)),16,Theme.key_windowBackgroundWhiteBlackText);label.setPaddingRelative(dp(16),0,0,0);row.addView(label,new LinearLayout.LayoutParams(0,-2,1));
            sections.addView(row,new LinearLayout.LayoutParams(-1,-2));
            if(sections.getChildCount()<preset.sections.size()*2-1){View separator=new View(c);separator.setBackgroundColor(color(Theme.key_divider));sections.addView(separator,new LinearLayout.LayoutParams(-1,1));}
        }
        add(all,sections,0,14);add(all,text(getString(R.string.FlexyStudioApplyInfo),14,Theme.key_windowBackgroundWhiteGrayText2),0,14);
        LinearLayout buttons=new LinearLayout(c);buttons.setGravity(Gravity.CENTER_VERTICAL);
        TextView cancel=button(getString(R.string.Cancel),false);apply=button(getString(R.string.FlexyStudioApply),true);
        LinearLayout.LayoutParams half=new LinearLayout.LayoutParams(0,-2,1);half.setMarginEnd(dp(10));buttons.addView(cancel,half);buttons.addView(apply,new LinearLayout.LayoutParams(0,-2,1));
        cancel.setOnClickListener(v->{if(!busy)dismiss();});
        apply.setOnClickListener(v->{
            if(busy)return;BaseFragment f=owner.get();if(f==null||f.getParentActivity()==null){dismiss();return;}
            busy=true;apply.setEnabled(false);apply.setText(getString(R.string.FlexyStudioApplying));
            WeakReference<FlexyStudioSheet> weakSheet=new WeakReference<>(this);
            boolean accepted=FlexyStudioStore.apply(preset,(ok,recovery,receipt)->{
                FlexyStudioSheet sheet=weakSheet.get();if(sheet==null)return;
                sheet.busy=false;BaseFragment current=sheet.owner.get();
                if(ok){sheet.dismiss();if(current!=null&&current.getParentActivity()!=null)BulletinFactory.of(current).createSimpleBulletin(0,getString(R.string.FlexyStudioApplied),getString(R.string.UndoNoCaps),()->confirmUndo(current,receipt)).show();}
                else {sheet.apply.setEnabled(true);sheet.apply.setText(getString(R.string.FlexyStudioApply));FlexyStyleInstallHelper.error(current,recovery?R.string.FlexyStudioRecoveryPending:R.string.FlexyStudioApplyError);}
            });
            if(!accepted){busy=false;apply.setEnabled(true);apply.setText(getString(R.string.FlexyStudioApply));FlexyStyleInstallHelper.error(f,R.string.FlexyStudioBusy);}
        });
        all.addView(buttons,new LinearLayout.LayoutParams(-1,-2));
        ScrollView scroll=new ScrollView(c){@Override protected void onMeasure(int w,int h){super.onMeasure(w,MeasureSpec.makeMeasureSpec(Math.min(MeasureSpec.getSize(h),Math.max(dp(160),(int)(AndroidUtilities.displaySize.y*.86f))),MeasureSpec.AT_MOST));}};
        scroll.setFillViewport(false);scroll.addView(all,new ScrollView.LayoutParams(-1,-2));setCustomView(scroll);
    }
    private static void confirmUndo(BaseFragment owner,app.flexygram.studio.core.StudioTransaction.Receipt receipt) {
        owner.showDialog(new AlertDialog.Builder(owner.getParentActivity(),owner.getResourceProvider()).setTitle(getString(R.string.UndoNoCaps)).setMessage(getString(R.string.FlexyStudioUndoQuestion))
            .setPositiveButton(getString(R.string.UndoNoCaps),(d,w)->{
                if(!FlexyStudioStore.undo(receipt,(ok,pending,r)->{if(!ok)FlexyStyleInstallHelper.error(owner,pending?R.string.FlexyStudioRecoveryPending:R.string.FlexyStudioUndoConflict);}))FlexyStyleInstallHelper.error(owner,R.string.FlexyStudioBusy);
            }).setNegativeButton(getString(R.string.Cancel),null).create());
    }
    private int color(int key){return Theme.getColor(key,provider);}
    private TextView text(String value,int size,int key){TextView t=new TextView(getContext());t.setText(value);t.setTextSize(size);t.setTextColor(color(key));t.setTextDirection(View.TEXT_DIRECTION_LOCALE);t.setGravity(Gravity.START);return t;}
    private LinearLayout panel(Context c){LinearLayout view=new LinearLayout(c);view.setPadding(dp(14),dp(14),dp(14),dp(14));GradientDrawable shape=new GradientDrawable();shape.setColor(color(Theme.key_windowBackgroundWhite));shape.setCornerRadius(dp(18));shape.setStroke(dp(1),color(Theme.key_divider));view.setBackground(shape);return view;}
    private TextView button(String label,boolean primary){TextView b=text(label,16,primary?Theme.key_featuredStickers_buttonText:Theme.key_windowBackgroundWhiteBlueText);b.setGravity(Gravity.CENTER);b.setFocusable(true);b.setAccessibilityDelegate(new View.AccessibilityDelegate(){@Override public void onInitializeAccessibilityNodeInfo(View host,android.view.accessibility.AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(host,info);info.setClassName("android.widget.Button");}});b.setMinHeight(dp(50));b.setPadding(dp(12),dp(12),dp(12),dp(12));b.setBackground(Theme.createSimpleSelectorRoundRectDrawable(dp(18),color(primary?Theme.key_featuredStickers_addButton:Theme.key_windowBackgroundWhite),color(Theme.key_listSelector)));return b;}
    private void add(LinearLayout parent,View child,int top,int bottom){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=dp(top);p.bottomMargin=dp(bottom);parent.addView(child,p);}
    @Override protected boolean canDismissWithSwipe(){return !busy&&super.canDismissWithSwipe();}
}
