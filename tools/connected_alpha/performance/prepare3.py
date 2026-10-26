#!/usr/bin/env python3
"""Prepare reversible production records and an UNAPPLIED shared-compositor animation candidate."""
import difflib,subprocess
from pathlib import Path
from universal_contract import BASE,ROOT,PRODUCTION,clean_context
HERE=Path(__file__).resolve().parent

def patch(path,before,after):
 if before==after:return ''
 return 'diff --git a/'+path+' b/'+path+'\n'+''.join(clean_context(list(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+path,tofile='b/'+path))))

def motion():
 path='TMessagesProj/src/main/java/org/telegram/ui/Components/ReplaceableIconDrawable.java';before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True);after=before
 after=after.replace('''        if (drawable == null) {
            currentDrawable = null;''','''        if (drawable == null) {
            cancelAnimation();
            currentResId = 0;
            progress = 1f;
            currentDrawable = null;''',1)
 after=after.replace('''        if (animation != null) {
            animation.removeAllListeners();
            animation.cancel();
        }''','''        cancelAnimation();''',1)
 after=after.replace('''            outDrawable = null;
            return;''','''            outDrawable = null;
            invalidateSelf();
            return;''',1)
 after=after.replace('''    @Override
    protected void onBoundsChange''','''    private void cancelAnimation() {
        ValueAnimator previous = animation;
        animation = null;
        if (previous != null) {
            previous.removeAllListeners();
            previous.removeAllUpdateListeners();
            previous.cancel();
        }
    }

    @Override
    protected void onBoundsChange''',1)
 after=after.replace('''    public void onAnimationEnd(Animator animation) {
        outDrawable = null;''','''    public void onAnimationEnd(Animator animation) {
        if (this.animation != animation) return;
        this.animation = null;
        outDrawable = null;''',1)
 return path,before,after
if __name__=='__main__':
 for path in sorted(PRODUCTION):
  before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True);after=(ROOT/path).read_text();name='flicker3.patch'if'CellFlicker'in path else'clip3.patch';(HERE/name).write_text(patch(path,before,after))
 path,before,after=motion();(HERE/'motion3.patch').write_text(patch(path,before,after))
 print('Prepared two exact production deltas; motion candidate NOT applied to application sources')
