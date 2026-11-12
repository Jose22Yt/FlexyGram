package org.telegram.ui.Wallet;

/** UI-thread request ownership for read-only wallet state; never holds keys or balances. */
public final class WalletLoadState {
    private long generation;
    private boolean loading;
    private String error;
    public long begin() { loading = true; error = null; return ++generation; }
    public boolean owns(long token) { return loading && generation == token; }
    public boolean finish(long token, String failure) {
        if (!owns(token)) return false;
        loading = false;
        error = failure;
        return true;
    }
    public void cancel() { generation++; loading = false; error = null; }
    public void clearError() { error = null; }
    public void setError(String failure) { if (!loading) error = failure; }
    public boolean isLoading() { return loading; }
    public String getError() { return error; }
}
