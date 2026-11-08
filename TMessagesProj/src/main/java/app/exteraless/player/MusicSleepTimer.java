package app.exteraless.player;

import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import org.telegram.messenger.MediaController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.UserConfig;

/** One session timer, independent of the player view. Never retains a fragment or an activity. */
final class MusicSleepTimer implements NotificationCenter.NotificationCenterDelegate {
    private static final MusicSleepTimer INSTANCE = new MusicSleepTimer();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private long deadline;
    private int account;
    private boolean observing;
    private final Runnable stop = () -> {
        if (deadline == 0) return;
        MessageObject message = MediaController.getInstance().getPlayingMessageObject();
        if (message != null && message.isMusic() && message.currentAccount == account)
            MediaController.getInstance().pauseMessage(message);
        cancel();
    };
    static MusicSleepTimer get() { return INSTANCE; }
    void start(int minutes) {
        cancel();
        MessageObject message=MediaController.getInstance().getPlayingMessageObject();
        if (minutes <= 0 || message == null || !message.isMusic()) return;
        account=message.currentAccount;long delay=minutes*60_000L;deadline=SystemClock.elapsedRealtime()+delay;
        handler.postDelayed(stop,delay);observing=true;
        for (int a=0;a<UserConfig.MAX_ACCOUNT_COUNT;a++) {
            NotificationCenter nc=NotificationCenter.getInstance(a);
            nc.addObserver(this,NotificationCenter.messagePlayingDidReset);
            nc.addObserver(this,NotificationCenter.messagePlayingDidStart);
        }
    }
    void cancel() {
        deadline=0;handler.removeCallbacks(stop);
        if (observing) for (int a=0;a<UserConfig.MAX_ACCOUNT_COUNT;a++) {
            NotificationCenter nc=NotificationCenter.getInstance(a);
            nc.removeObserver(this,NotificationCenter.messagePlayingDidReset);
            nc.removeObserver(this,NotificationCenter.messagePlayingDidStart);
        }
        observing=false;
    }
    long remainingMinutes() {
        if (deadline != 0 && SystemClock.elapsedRealtime() >= deadline) stop.run();
        return deadline==0?0:Math.max(1,(deadline-SystemClock.elapsedRealtime()+59_999)/60_000);
    }
    @Override public void didReceivedNotification(int id,int currentAccount,Object...args) {
        MessageObject message=MediaController.getInstance().getPlayingMessageObject();
        if (message==null || !message.isMusic() || message.currentAccount!=account) cancel();
    }
}
