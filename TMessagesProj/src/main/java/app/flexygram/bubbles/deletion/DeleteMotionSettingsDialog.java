package app.flexygram.bubbles.deletion;

import android.app.Activity;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.LaunchActivity;

/** Compatibility entry point; the selector now uses the standard FlexyGram settings page. */
public final class DeleteMotionSettingsDialog {
    private DeleteMotionSettingsDialog(){}
    public static void show(Activity activity){
        BaseFragment fragment=LaunchActivity.getLastFragment();
        if(activity!=null && !activity.isFinishing() && fragment!=null && fragment.getParentActivity()==activity)
            fragment.presentFragment(new DeleteMotionSettingsActivity());
    }
}
