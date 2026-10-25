/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;
import android.app.job.*;
import org.telegram.messenger.AndroidUtilities;
import java.util.concurrent.Future;
/** One-shot cache expiry after sharing. No periodic scanner or resident service. */
public final class FlexyStudioCleanup extends JobService {
    private Future<?> work;
    @Override public boolean onStartJob(JobParameters parameters) {
        try{work=FlexyStudioIO.execute(()->{FlexyStudioFiles.cleanup(getApplicationContext(),8);AndroidUtilities.runOnUIThread(()->jobFinished(parameters,false));});return true;}
        catch(java.util.concurrent.RejectedExecutionException busy){jobFinished(parameters,true);return true;}
    }
    @Override public boolean onStopJob(JobParameters parameters){FlexyStudioIO.cancel(work);return true;}
}
