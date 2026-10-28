import org.telegram.ui.ActionBar.FlexyInstantNavigationCoordinator;
import static org.telegram.ui.ActionBar.FlexyInstantNavigationCoordinator.*;

/** Actual coordinator, dependency-free JVM protocol tests; not Android/device latency. */
public final class InstantNavigationCoordinatorTest {
    static int assertions;
    static void check(boolean result) { assertions++; if (!result) throw new AssertionError("case " + assertions); }
    static Intent chat(long id) { return new Intent(Kind.OPEN_CHAT, id, null); }
    public static void main(String[] args) throws Exception {
        var c = new FlexyInstantNavigationCoordinator();
        check(c.state() == State.IDLE && c.intent() == null);
        int[] calls = {0};
        long first = c.begin(State.CLOSING, new Intent(Kind.REVEAL_SURFACE, 0, "main"), true);
        check(c.commit(first, () -> calls[0]++));
        check(calls[0] == 1 && c.state() == State.IDLE && c.intent() == null);
        check(!c.commit(first, () -> calls[0]++));
        check(calls[0] == 1);
        long a = c.begin(State.OPENING, chat(-123456789L), false);
        check(c.intent().destinationId == -123456789L);
        check(!c.commit(a, () -> calls[0]++));
        long b = c.begin(State.OPENING, chat(456), false);
        check(!c.complete(a) && !c.cancel(a) && c.intent().destinationId == 456);
        check(c.complete(b) && !c.complete(b));
        long commit = c.begin(State.CLOSING, chat(1), true);
        check(!c.commit(commit, () -> c.begin(State.OPENING, chat(2), false)));
        check(c.state() == State.OPENING && c.intent().destinationId == 2);
        check(!c.complete(commit) && !c.cancel(commit));
        check(c.complete(c.generation()));
        long recursive = c.begin(State.SETTLING, chat(3), true);
        check(c.commit(recursive, () -> {
            check(!c.commit(recursive, () -> { throw new AssertionError("double commit"); }));
            check(!c.complete(recursive));
        }));
        long failed = c.begin(State.CLOSING, chat(4), true);
        try { c.commit(failed, () -> { throw new IllegalStateException("fixture failure"); }); throw new AssertionError(); }
        catch (IllegalStateException expected) { check(c.state() == State.CANCELLED && c.intent() == null); }
        check(!c.commit(failed, () -> calls[0]++));
        long newer = c.begin(State.CLOSING, chat(5), true);
        try { c.commit(newer, () -> { c.begin(State.OPENING, chat(6), false); throw new IllegalStateException("old failure"); }); }
        catch (IllegalStateException expected) { check(c.state() == State.OPENING && c.intent().destinationId == 6); }
        check(c.complete(c.generation()));
        for (State gesture : new State[]{State.DRAGGING, State.OPENING, State.CLOSING, State.SETTLING}) {
            long token = c.begin(gesture, new Intent(Kind.MODAL, 0, "modal"), false);
            check(!c.commit(token, () -> calls[0]++));
            check(c.cancel(token) && !c.complete(token) && c.intent() == null);
        }
        for (int i = 0; i < 10000; i++) {
            long old = c.begin(State.CLOSING, chat(i), true);
            long next = c.begin(State.OPENING, chat(i + 1), false);
            check(!c.commit(old, () -> { throw new AssertionError("stale action"); }));
            check(!c.complete(old));
            check(c.complete(next));
        }
        Throwable[] error = {null};
        Thread other = new Thread(() -> { try { c.begin(State.OPENING, chat(7), false); } catch (Throwable e) { error[0] = e; } });
        other.start(); other.join();
        check(error[0] instanceof IllegalStateException && c.state() == State.IDLE);
        System.out.println("PASS coordinator protocol assertions=" + assertions + "; physical Android NOT_TESTED");
    }
}
