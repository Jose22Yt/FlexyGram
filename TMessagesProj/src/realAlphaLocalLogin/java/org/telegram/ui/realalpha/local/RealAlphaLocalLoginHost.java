package org.telegram.ui.realalpha.local;

import android.content.Context;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.SystemClock;
import java.util.concurrent.Executor;
import java.lang.ref.WeakReference;
import java.util.concurrent.atomic.AtomicBoolean;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.LaunchActivity;
import org.telegram.ui.LoginActivity;
import org.telegram.ui.DialogsActivity;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.ActionBarMenu;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.realalpha.RealAlphaActivity;
import org.telegram.ui.realalpha.RealAlphaPolicy;
import io.github.jose22yt.flexygram.session.AuthenticationController;
import io.github.jose22yt.flexygram.session.android.*;

/** Explicit native menu entry; owns only a short-lived, local rehearsal, never an account session. */
public final class RealAlphaLocalLoginHost implements AutoCloseable {
    private static final int MENU_ID = 904301;
    private enum Phase { NATIVE_ATTESTATION, ACCOUNT_INSPECTION, LOCAL_INITIALIZATION, PRESENTATION }
    private final RealAlphaActivity activity;
    private final Handler main = new Handler(Looper.getMainLooper());
    private Ticket current;
    private LocalScreen screen;
    private boolean closed, choosing;
    private static final class Ticket {
        final HandlerThread thread = new HandlerThread("FlexyGramLocalLogin");
        final AtomicBoolean cancelled = new AtomicBoolean();
        final Handler worker;
        volatile LocalLoginRehearsal flow;
        volatile Phase phase=Phase.NATIVE_ATTESTATION;
        Ticket() { thread.start(); worker=new Handler(thread.getLooper()); }
        Executor executor() { return task -> { if (!worker.post(task)) throw new IllegalStateException("LOCAL_WORKER_UNAVAILABLE"); }; }
        void close() {
            if (!cancelled.compareAndSet(false,true)) return;
            LocalLoginRehearsal owned=flow;
            if (owned!=null) owned.close();
            // Owner teardown is enqueued first; no permanent background process is created.
            if (!worker.post(thread::quitSafely)) thread.quitSafely();
        }
    }
    public RealAlphaLocalLoginHost(RealAlphaActivity activity) {
        if (activity==null) throw new IllegalArgumentException("LOCAL_HOST_REQUIRED");
        this.activity=activity;
    }
    public void attachEntry() {
        requireMain(); RealAlphaPolicy.requireClosedBuild();
        if (closed || activity.isFinishing()) return;
        BaseFragment root=LaunchActivity.getLastFragment();
        if (root==null || root.getClass()!=DialogsActivity.class) return;
        ActionBar bar=root.getActionBar(); if (bar==null) return;
        ActionBarMenu menu=bar.createMenu();
        org.telegram.ui.ActionBar.ActionBarMenuItem item=menu.getItem(MENU_ID);
        if (item==null) item=menu.addItem(MENU_ID,"Login local");
        // A native DialogsActivity/menu may survive Activity recreation. Always rebind it.
        WeakReference<RealAlphaLocalLoginHost> host=new WeakReference<>(this);
        WeakReference<BaseFragment> origin=new WeakReference<>(root);
        item.setOnClickListener(v -> {
            RealAlphaLocalLoginHost active=host.get(); BaseFragment owner=origin.get();
            if (active!=null && owner!=null) active.choose(owner);
        });
    }
    private void choose(BaseFragment root) {
        requireMain();
        if (closed || current!=null || choosing || activity.isFinishing() || LaunchActivity.getLastFragment()!=root) return;
        if (AndroidUtilities.isTablet()) { status(root,"LOCAL_PHONE_LAB_ONLY"); return; }
        choosing=true;
        AlertDialog dialog=new AlertDialog.Builder(activity)
            .setTitle("Laboratorio local — sin Telegram")
            .setItems(new CharSequence[]{"SMS — código 000000","APP — código 000000","2FA simulada — código 000000","Registro simulado — código 000000"},
                (d,which) -> { choosing=false; if (which>=0 && which<4) open(root,LocalLoginRehearsal.Scenario.values()[which]); })
            .create();
        dialog.setOnDismissListener(d -> choosing=false);
        root.showDialog(dialog);
    }
    private void open(BaseFragment root,LocalLoginRehearsal.Scenario scenario) {
        requireMain(); RealAlphaPolicy.requireClosedBuild();
        if (closed || current!=null || LaunchActivity.getLastFragment()!=root) return;
        final int account=root.getCurrentAccount();
        final Context application=activity.getApplicationContext();
        final Ticket ticket;
        try { ticket=new Ticket(); } catch (RuntimeException|LinkageError failure) { status(root,"LOCAL_WORKER_UNAVAILABLE"); return; }
        current=ticket;
        if (!ticket.worker.post(() -> {
            try {
                if (ticket.cancelled.get()) return;
                ReadOnlyAttestation attestation=AndroidNativeBridge.read(application,account);
                ticket.phase=Phase.ACCOUNT_INSPECTION;
                AccountProbe.Snapshot probe=new TelegramAccountAdapter(application,attestation).inspect();
                if (probe.evidence!=AccountProbe.Evidence.EMPTY || !probe.controllerHandlesAvailable)
                    throw new IllegalStateException("LOCAL_ACCOUNT_NOT_EMPTY");
                ticket.phase=Phase.LOCAL_INITIALIZATION;
                LocalLoginRehearsal flow=new LocalLoginRehearsal(attestation.runtime,scenario,ticket.executor(),SystemClock::elapsedRealtime);
                ticket.flow=flow;
                if (ticket.cancelled.get()) { flow.close(); ticket.thread.quitSafely(); return; }
                if (!flow.initialize()) throw new IllegalStateException("LOCAL_INITIALIZATION_REJECTED");
                ticket.executor().execute(() -> {
                    if (!main.post(() -> ready(root,account,ticket))) ticket.close();
                });
            } catch (RuntimeException|LinkageError failure) {
                if (!main.post(() -> failed(root,ticket))) ticket.close();
            }
        })) failed(root,ticket);
    }
    private void ready(BaseFragment root,int account,Ticket ticket) {
        requireMain();
        if (closed || current!=ticket || ticket.cancelled.get() || activity.isFinishing()
                || LaunchActivity.getLastFragment()!=root || root.getCurrentAccount()!=account) { ticket.close(); if(current==ticket)current=null; return; }
        if (ticket.flow==null || ticket.flow.owner.snapshot().state!=AuthenticationController.State.READY) { failed(root,ticket); return; }
        try {
            ticket.phase=Phase.PRESENTATION;
            LocalScreen candidate=new LocalScreen(account,ticket,this);
            screen=candidate; // Admission identity is installed before native presentation delegates run.
            if (!root.presentFragment(candidate) && candidate.getParentLayout()==null) failed(root,ticket);
        } catch (RuntimeException|LinkageError failure) { failed(root,ticket); }
    }
    public boolean owns(BaseFragment fragment) {
        return !closed && current!=null && !current.cancelled.get() && fragment!=null && fragment==screen;
    }
    private void failed(BaseFragment root,Ticket ticket) {
        requireMain(); ticket.close();
        if (current!=ticket) return;
        current=null; screen=null;
        if (!closed && !activity.isFinishing() && LaunchActivity.getLastFragment()==root) status(root,"LOCAL_LOGIN_UNAVAILABLE:"+ticket.phase.name());
    }
    private void status(BaseFragment root,String code) {
        root.showDialog(new AlertDialog.Builder(activity).setTitle("Laboratorio local")
            .setMessage(code+"\nNo se ha conectado Telegram ni cambiado ninguna sesión.")
            .setPositiveButton("OK",null).create());
    }
    private static final class LocalScreen extends LoginActivity {
        private final WeakReference<RealAlphaLocalLoginHost> host;
        private final Ticket ticket;
        LocalScreen(int account,Ticket ticket,RealAlphaLocalLoginHost host) { super(account); this.ticket=ticket; this.host=new WeakReference<>(host); bindClosedLocalPages(ticket.flow.pages); }
        @Override public void onFragmentDestroy() {
            try { super.onFragmentDestroy(); }
            finally { ticket.close(); RealAlphaLocalLoginHost active=host.get(); if (active!=null && active.current==ticket) { active.current=null; active.screen=null; } host.clear(); }
        }
    }
    @Override public void close() {
        requireMain(); closed=true; choosing=false;
        Ticket ticket=current; current=null; screen=null;
        if (ticket!=null) ticket.close();
    }
    private static void requireMain() {
        if (Looper.myLooper()!=Looper.getMainLooper()) throw new IllegalStateException("LOCAL_UI_REQUIRES_MAIN");
    }
}
