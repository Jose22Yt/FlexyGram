package app.flexygram.performance;

/** Only delays a brief initial-data label; connection and message synchronization stay native. */
public final class StartupStatus {
    public static final long INITIAL_LABEL_DELAY_MS = 350;
    private int account = -1;
    private long started = -1;
    public long remaining(int currentAccount, long now, boolean waitingForInitialData) {
        if (!waitingForInitialData) { reset(); return 0; }
        if (account != currentAccount || started < 0 || now < started) {
            account = currentAccount;
            started = now;
        }
        return Math.max(0, INITIAL_LABEL_DELAY_MS - (now - started));
    }
    public void reset() { account = -1; started = -1; }
}
