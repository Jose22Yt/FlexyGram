"""Real DOWN/UP + exact native click, reveal ownership and both analytic renderers.

Fragment creation/stack mutation, account/services and slide transactions remain
explicit doubles. This is not the full RecyclerView, Activity or physical OS.
"""
from player_probe import method
import re

def write(put,root):
 from gesture_opening_probe import write as gesture
 captured={};gesture(lambda n,c:captured.update({n:c}),root)
 code=captured['GestureOpeningProbe.java'].replace('GestureOpeningProbe','RevealProbe')
 source=(root/'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
 # Replace only inactive legacy scaffolding. Active P11 tests execute all actual helpers.
 for signature in ['void clearInstantRevealTouch(', 'void settleInstantRevealTouch(', 'void setInstantRevealTranslationX(']:
  code=code.replace(method(code,signature),'',1)
 a=source.index('    // A real exposed-list touch');b=source.index('    private void clearInstantBackSeed()',a)
 reveal=source[a:b]
 # Seed primitives/method are already copied by the existing native probe fixture.
 seed_a=reveal.index('    private boolean instantRevealSeed;');seed_b=reveal.index('    private void clearInstantRevealTouch(',seed_a)
 reveal=reveal[:seed_a]+reveal[seed_b:]
 reveal=re.sub(r'\bViewGroup\b','android.view.ViewGroup',reveal)
 reveal=re.sub(r'\bView\b','android.view.View',reveal)
 code=code.replace('import java.util.*;', 'import java.util.*;import android.view.MotionEvent;import org.telegram.ui.ActionBar.FlexyNavigationHandoffPolicy;')
 # Existing constructor's two containers are real; the home is a deterministic non-private row.
 code=code.replace('fragmentsStack.add(new BaseFragment());','fragmentsStack.add(new MainTabsActivity());',1)
 code=code.replace('static class ChatActivity extends BaseFragment', 'static class MainTabsActivity extends BaseFragment{}static class DialogsActivity extends BaseFragment{}static class ChatActivity extends BaseFragment')
 code=code.replace('static class BaseFragment {', 'static class BaseFragment {int creates,destroys;boolean createAllowed=true,deferred;Runnable onCreate;boolean onFragmentCreate(){creates++;if(onCreate!=null)onCreate.run();return createAllowed;}void onFragmentDestroy(){destroys++;}AttachedSheet getLastSheet(){return null;}')
 code=code.replace('interface AttachedSheet{','interface AttachedSheet{default android.view.View getWindowView(){return null;}')
 code=code.replace('public RevealProbe(android.content.Context c){super(c);','public RevealProbe(android.content.Context c){super(c);')
 # Include the original native dispatch body, and the exact new paint hook in a real drawChild.
 dispatch=method(source,'    private boolean dispatchNativeRevealTouch(')
 detach=method(source,'    protected void onDetachedFromWindow(')
 # Keep the real framework surface; hide only test access modifiers of metadata/helpers.
 reveal=reveal.replace('private ','')
 reveal=reveal.replace('@Override\n    public boolean presentFragment(', 'public boolean presentFragment(')
 body=reveal+'\n'+dispatch+'\n'+detach+'\n'+method(source,'    public boolean onInterceptTouchEvent(')
 body+='''
 boolean attached,tabsEvents;android.graphics.Rect systemAndDisplayInsets=new android.graphics.Rect();int getBottomTabsHeight(boolean ignored){return 0;}
 __FALLBACK__
 protected boolean drawChild(android.graphics.Canvas canvas,android.view.View child,long time){int save=canvas.save();
'''
 paint='        if (child == instantRevealSurface) canvas.translate(instantRevealDrawX - instantRevealHitX, 0);'
 assert source.count(paint)==1
 body+=paint+'''boolean result=super.drawChild(canvas,child,time);canvas.restoreToCount(save);return result;}
 static class NavigationParams{BaseFragment fragment;boolean removeLast,noAnimation,checkPresentFromDelegate=true,preview;Object menuView;NavigationParams(BaseFragment f){fragment=f;}}
 Runnable afterClose;int opens,clicks,downs,ups,cancels;boolean veto;boolean nextPreview,nextRemove,nextNoAnimation;BaseFragment nextTarget;long downStamp,upStamp;float downX,upX;ChatActivity target;NativeRow row;
 void installRow(){containerViewBack.removeAllViews();row=new NativeRow();org.telegram.ui.Components.RecyclerListView list=new org.telegram.ui.Components.RecyclerListView(getContext());containerViewBack.addView(list,new android.widget.FrameLayout.LayoutParams(300,600));list.addView(row,new android.widget.FrameLayout.LayoutParams(300,96));row.setY(200);containerView.setBackgroundColor(0xffcc3333);containerViewBack.setBackgroundColor(0xff33aa55);}
 void replaceAcceptedScene(){BaseFragment replacement=new SettingsActivity();fragmentsStack.set(fragmentsStack.size()-1,replacement);reportInstantNavigation(org.telegram.ui.ActionBar.FlexyInstantNavigationCoordinator.State.OPENING,replacement,org.telegram.ui.ActionBar.FlexyInstantNavigationCoordinator.Kind.OPEN_SCREEN);transitionAnimationInProgress=true;onOpenAnimationEndRunnable=()->{};currentSpringAnimation=new app.flexygram.motion.SpringAnimation(this,new androidx.dynamicanimation.animation.FloatValueHolder(0)).setSpring(new androidx.dynamicanimation.animation.SpringForce(1000));currentSpringAnimation.start();containerView.setTranslationX(123);inner=123;}
 void beginOrdinaryClose(){beginClose(getLastFragment());}
'''
 # Exact native admission through report/try ownership; subsequent view/stack creation is explicitly doubled.
 a=source.index('    private boolean presentNativeRevealFragment(NavigationParams params)');b=source.index('        final EdgeToEdgeSupportMode',a)
 admission=source[a:b].replace('ActionBarPopupWindow.ActionBarPopupWindowLayout menu','Object menu')
 body+=admission+'''
        opens++;BaseFragment home=getLastFragment();fragmentsStack.add(fragment);oldFragment=home;newFragment=fragment;
        Container previous=containerView;containerView=containerViewBack;containerViewBack=previous;
        containerView.setVisibility(android.view.View.VISIBLE);containerViewBack.setVisibility(android.view.View.VISIBLE);containerView.setTranslationX(getWidth()-getPaddingLeft()-getPaddingRight());containerView.setScaleX(.85f);containerView.setScaleY(.85f);containerViewBack.setTranslationX(0);containerView.removeAllViews();containerView.addView(new android.view.View(getContext()),new android.widget.FrameLayout.LayoutParams(300,600));containerView.setBackgroundColor(0xff3344cc);bringChildToFront(containerView);
        transitionAnimationInProgress=true;transitionAnimationStartTime=System.currentTimeMillis();onOpenAnimationEndRunnable=()->{};
        if(!fragment.deferred) startNativeSpring(true,false);
        return true;
    }
'''
 # Use the same P6 settling spring branch (real actor/renderer); initial release and slide mutation are doubled.
 a=source.index('        if (USE_SPRING_ANIMATION) {',source.index('    private void animateBackEndAnimation('))
 spring=method(source[a:],'        if (USE_SPRING_ANIMATION)')
 body+='void stageReleased(float q){float velX=0,x=q*300;boolean backAnimation=false;startedTracking=true;containerView.setTranslationX(x);containerView.setScaleX(1-.15f*q);containerView.setScaleY(1-.15f*q);containerViewBack.setTranslationX(-(1-q)*.35f*300);'+spring+'}'
 # Actual RecyclerListView click decoder, real GestureDetector/Views; the adapter/account listener is doubled.
 r=(root/'TMessagesProj/src/main/java/org/telegram/ui/Components/RecyclerListView.java').read_text()
 press=re.sub(r'\bView\b','android.view.View',method(r,'                private void onPressItem('))
 tap=method(r,'                public boolean onSingleTapUp(')
 body+='''
 interface Click{void onItemClick(android.view.View view,int position);}
 interface ExtendedClick{boolean hasDoubleTap(android.view.View view,int position);void onItemClick(android.view.View view,int position,float x,float y);}
 class NativeRow extends org.telegram.ui.Cells.DialogCell {
  android.view.View currentChildView=this,doubleTapView;int currentChildPosition;boolean instantClick=true,interceptedByChild;Runnable clickRunnable,selectChildRunnable;
  Click onItemClickListener=(v,p)->{clicks++;target=nextTarget instanceof ChatActivity?(ChatActivity)nextTarget:new ChatActivity();NavigationParams params=new NavigationParams(nextTarget==null?target:nextTarget);params.preview=nextPreview;params.removeLast=nextRemove;params.noAnimation=nextNoAnimation;presentFragment(params);};ExtendedClick onItemClickListenerExtended;
  void onChildPressed(android.view.View view,float x,float y,boolean pressed){view.setPressed(pressed);}void removeSelection(android.view.View view,MotionEvent event){}
  final android.view.GestureDetector detector;
  NativeRow(){super(RevealProbe.this.getContext());setBackgroundColor(0xff33aa55);detector=new android.view.GestureDetector(getContext(),new android.view.GestureDetector.SimpleOnGestureListener(){public boolean onDown(MotionEvent event){currentChildView=NativeRow.this;return true;}
'''+tap+'''
  });}
  public boolean onTouchEvent(MotionEvent event){int a=event.getActionMasked();if(a==MotionEvent.ACTION_DOWN){downs++;downStamp=event.getEventTime();downX=event.getX();}if(a==MotionEvent.ACTION_UP){ups++;upStamp=event.getEventTime();upX=event.getX();}if(a==MotionEvent.ACTION_CANCEL)cancels++;return detector.onTouchEvent(event);}
'''+press+'\n }'
 code=code.replace('fragmentsStack.remove(target);inPreviewMode=false;', 'target.onFragmentDestroy();fragmentsStack.remove(target);containerViewBack.removeAllViews();containerViewBack.setVisibility(android.view.View.GONE);if(afterClose!=null)afterClose.run();inPreviewMode=false;')
 code=code.replace('static class AndroidUtilities{','static class AndroidUtilities{static final android.os.Handler revealHandler=new android.os.Handler(android.os.Looper.getMainLooper());static void runOnUIThread(Runnable r,long delay){revealHandler.postDelayed(r,delay);}')
 code=code.replace('import android.animation.Animator;', 'import android.view.SoundEffectConstants;import android.view.ViewConfiguration;import android.view.accessibility.AccessibilityEvent;import android.animation.Animator;')
 code=code.replace('interface Delegate{boolean needCloseLastFragment(RevealProbe p);}', 'interface Delegate{boolean needCloseLastFragment(RevealProbe p);default boolean needPresentFragment(RevealProbe p,NavigationParams params){return !p.veto;}}')
 # Explicit slide transaction double swaps the same actual containers as the native P6 lifecycle.
 slide=method(code,' void onSlideAnimationEnd(')
 slide_new=slide.replace('if(!revert)fragmentsStack.remove(fragmentsStack.size()-1);','if(!revert){getLastFragment().onFragmentDestroy();fragmentsStack.remove(fragmentsStack.size()-1);Container previous=containerView;containerView=containerViewBack;containerViewBack=previous;containerViewBack.setVisibility(android.view.View.GONE);}')
 slide_new=slide_new[:-1]+'settleInstantRevealTouch();}'
 code=code.replace(slide,slide_new)
 body=body.replace('__FALLBACK__',method(source,'    private boolean tryHandoffSettlingChatDown(')+'\n'+method(source,'    private boolean tryHandoffClosingChatDown('))
 code=code[:code.rfind('}')]+body+'\n}'
 put('RevealProbe.java',code)
