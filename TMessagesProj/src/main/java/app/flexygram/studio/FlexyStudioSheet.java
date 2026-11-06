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
    private final java.util.Set<String> selected=new java.util.LinkedHashSet<>();
    public FlexyStudioSheet(BaseFragment fragment,StudioCodec.Preset preset,String filename,int bytes,StudioImportPlan plan) {
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
        selected.addAll(plan.defaultSelection());
        for(StudioImportPlan.Group group:plan.groups) {
            String id=group.id;
            LinearLayout block=new LinearLayout(c);block.setOrientation(LinearLayout.VERTICAL);
            LinearLayout row=new LinearLayout(c);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(16),dp(10),dp(12),dp(10));row.setMinimumHeight(dp(56));
            LinearLayout labels=new LinearLayout(c);labels.setOrientation(LinearLayout.VERTICAL);
            labels.addView(text(getString(FlexyStudioText.section(id)),16,Theme.key_windowBackgroundWhiteBlackText));
            TextView count=text("",13,Theme.key_windowBackgroundWhiteGrayText2);labels.addView(count);
            row.addView(labels,new LinearLayout.LayoutParams(0,-2,1));
            CheckBox check=new CheckBox(c);check.setButtonTintList(android.content.res.ColorStateList.valueOf(color(Theme.key_windowBackgroundWhiteBlueText)));check.setEnabled(!group.changes.isEmpty());
            check.setContentDescription(getString(FlexyStudioText.section(id)));row.addView(check,new LinearLayout.LayoutParams(dp(48),dp(48)));
            boolean[] binding={false};
            Runnable refreshGroup=()->{
                int included=0;for(StudioImportPlan.Change change:group.changes)if(selected.contains(StudioImportPlan.selectionKey(group,change)))included++;
                binding[0]=true;check.setChecked(included>0&&included==group.changes.size());binding[0]=false;
                count.setText(group.changes.isEmpty()?getString(R.string.FlexyStudioAlreadyMatches):org.telegram.messenger.LocaleController.formatString("FlexyStudioSelectedCount",R.string.FlexyStudioSelectedCount,included,group.changes.size()));
                refreshApply();
            };
            LinearLayout details=new LinearLayout(c);details.setOrientation(LinearLayout.VERTICAL);details.setVisibility(View.GONE);
            int[] page={0};Runnable[] showPage={()->{}};
            check.setOnCheckedChangeListener((button,checked)->{
                if(binding[0])return;
                if(!busy)for(StudioImportPlan.Change change:group.changes){String key=StudioImportPlan.selectionKey(group,change);if(checked)selected.add(key);else selected.remove(key);}
                refreshGroup.run();if(details.getVisibility()==View.VISIBLE)showPage[0].run();
            });
            row.setOnClickListener(v->{if(check.isEnabled()&&!busy)check.performClick();});
            block.addView(row,new LinearLayout.LayoutParams(-1,-2));refreshGroup.run();
            if(!group.changes.isEmpty()) {
                TextView expand=text(getString(R.string.FlexyStudioViewChanges),14,Theme.key_windowBackgroundWhiteBlueText);expand.setPadding(dp(16),dp(8),dp(16),dp(12));expand.setMinHeight(dp(44));expand.setFocusable(true);
                LinearLayout paging=new LinearLayout(c);paging.setGravity(Gravity.CENTER_VERTICAL);paging.setVisibility(View.GONE);
                TextView previous=button(getString(R.string.FlexyStudioPreviousChanges),false),next=button(getString(R.string.FlexyStudioNextChanges),false);
                paging.addView(previous,new LinearLayout.LayoutParams(0,-2,1));paging.addView(next,new LinearLayout.LayoutParams(0,-2,1));
                showPage[0]=()->{
                    details.removeAllViews();int end=Math.min(page[0]+20,group.changes.size());
                    for(int i=page[0];i<end;i++){
                        StudioImportPlan.Change change=group.changes.get(i);String key=StudioImportPlan.selectionKey(group,change);
                        LinearLayout item=new LinearLayout(c);item.setGravity(Gravity.CENTER_VERTICAL);item.setPadding(dp(16),dp(6),dp(12),dp(6));item.setMinimumHeight(dp(48));
                        item.addView(text(describe(change),13,Theme.key_windowBackgroundWhiteGrayText2),new LinearLayout.LayoutParams(0,-2,1));
                        CheckBox option=new CheckBox(c);option.setButtonTintList(android.content.res.ColorStateList.valueOf(color(Theme.key_windowBackgroundWhiteBlueText)));option.setChecked(selected.contains(key));option.setContentDescription(describe(change));
                        option.setOnCheckedChangeListener((button,checked)->{if(busy){option.setChecked(selected.contains(key));return;}if(checked)selected.add(key);else selected.remove(key);refreshGroup.run();});
                        item.addView(option,new LinearLayout.LayoutParams(dp(48),dp(48)));item.setOnClickListener(v->{if(!busy)option.performClick();});details.addView(item,new LinearLayout.LayoutParams(-1,-2));
                    }
                    previous.setEnabled(page[0]>0);next.setEnabled(end<group.changes.size());
                };
                previous.setOnClickListener(v->{if(page[0]>0){page[0]-=20;showPage[0].run();}});
                next.setOnClickListener(v->{if(page[0]+20<group.changes.size()){page[0]+=20;showPage[0].run();}});
                expand.setOnClickListener(v->{boolean show=details.getVisibility()!=View.VISIBLE;if(show)showPage[0].run();details.setVisibility(show?View.VISIBLE:View.GONE);paging.setVisibility(show&&group.changes.size()>20?View.VISIBLE:View.GONE);expand.setText(getString(show?R.string.FlexyStudioHideChanges:R.string.FlexyStudioViewChanges));});
                block.addView(expand,new LinearLayout.LayoutParams(-1,-2));block.addView(details,new LinearLayout.LayoutParams(-1,-2));block.addView(paging,new LinearLayout.LayoutParams(-1,-2));
            }
            sections.addView(block,new LinearLayout.LayoutParams(-1,-2));
            if(sections.getChildCount()<plan.groups.size()*2-1){View separator=new View(c);separator.setBackgroundColor(color(Theme.key_divider));sections.addView(separator,new LinearLayout.LayoutParams(-1,1));}
        }
        add(all,sections,0,14);add(all,text(getString(R.string.FlexyStudioSelectiveInfo),14,Theme.key_windowBackgroundWhiteGrayText2),0,14);
        LinearLayout buttons=new LinearLayout(c);buttons.setGravity(Gravity.CENTER_VERTICAL);
        TextView cancel=button(getString(R.string.Cancel),false);apply=button(getString(R.string.FlexyStudioApply),true);refreshApply();
        LinearLayout.LayoutParams half=new LinearLayout.LayoutParams(0,-2,1);half.setMarginEnd(dp(10));buttons.addView(cancel,half);buttons.addView(apply,new LinearLayout.LayoutParams(0,-2,1));
        cancel.setOnClickListener(v->{if(!busy)dismiss();});
        apply.setOnClickListener(v->{
            if(busy||selected.isEmpty())return;BaseFragment f=owner.get();if(f==null||f.getParentActivity()==null){dismiss();return;}
            busy=true;apply.setEnabled(false);apply.setText(getString(R.string.FlexyStudioApplying));
            WeakReference<FlexyStudioSheet> weakSheet=new WeakReference<>(this);
            boolean accepted=FlexyStudioStore.applyChanges(plan,selected,(ok,recovery,receipt)->{
                FlexyStudioSheet sheet=weakSheet.get();if(sheet==null)return;
                sheet.busy=false;BaseFragment current=sheet.owner.get();
                if(ok){sheet.dismiss();if(current!=null&&current.getParentActivity()!=null)BulletinFactory.of(current).createSimpleBulletin(0,getString(R.string.FlexyStudioApplied),getString(R.string.UndoNoCaps),()->confirmUndo(current,receipt)).show();}
                else {sheet.refreshApply();sheet.apply.setText(getString(R.string.FlexyStudioApply));FlexyStyleInstallHelper.error(current,recovery?R.string.FlexyStudioRecoveryPending:R.string.FlexyStudioApplyError);}
            });
            if(!accepted){busy=false;refreshApply();apply.setText(getString(R.string.FlexyStudioApply));FlexyStyleInstallHelper.error(f,R.string.FlexyStudioBusy);}
        });
        all.addView(buttons,new LinearLayout.LayoutParams(-1,-2));
        ScrollView scroll=new ScrollView(c){@Override protected void onMeasure(int w,int h){super.onMeasure(w,MeasureSpec.makeMeasureSpec(Math.min(MeasureSpec.getSize(h),Math.max(dp(160),(int)(AndroidUtilities.displaySize.y*.86f))),MeasureSpec.AT_MOST));}};
        scroll.setFillViewport(false);scroll.addView(all,new ScrollView.LayoutParams(-1,-2));setCustomView(scroll);
    }
    private void refreshApply(){if(apply!=null)apply.setEnabled(!busy&&!selected.isEmpty());}
    private String describe(StudioImportPlan.Change change){
        if(change.key.equals("theme"))return getString(R.string.FlexyStudioThemeChange);
        return FlexyStudioText.setting(change.file,change.key)+": "+value(change.file,change.key,change.before)+" → "+value(change.file,change.key,change.after);
    }
    private String value(String file,String key,Object raw){
        if(raw instanceof java.util.Map){java.util.Map<?,?> map=(java.util.Map<?,?>)raw;
            if(Boolean.FALSE.equals(map.get("present")))return getString(R.string.FlexyStudioDefaultValue);
            if(Boolean.TRUE.equals(map.get("present")))return value(file,key,map.get("value"));
            StringBuilder text=new StringBuilder();int count=0;
            for(java.util.Map.Entry<?,?> item:map.entrySet()){
                if(count++==10){text.append("…");break;}
                if(text.length()>0)text.append(", ");
                text.append(item.getKey()).append("=").append(item.getValue());
            }
            return text.toString();
        }
        if(raw instanceof java.util.List){java.util.List<?> list=(java.util.List<?>)raw;StringBuilder text=new StringBuilder();for(int i=0;i<Math.min(10,list.size());i++){if(i>0)text.append(", ");String item=String.valueOf(list.get(i));text.append(item.substring(0,Math.min(30,item.length())));}if(list.size()>10)text.append("…");return text.toString();}
        if(raw instanceof Boolean)return getString((Boolean)raw?R.string.FlexyStudioEnabledValue:R.string.FlexyStudioDisabledValue);
        String choice=FlexyStudioText.choice(file,key,raw);if(choice!=null)return choice;
        String text=String.valueOf(raw).replace('\n',' ').replace('\r',' ');
        return text.length()>100?text.substring(0,100)+"…":text;
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
