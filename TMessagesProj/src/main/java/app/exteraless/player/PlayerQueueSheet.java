package app.exteraless.player;

import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.drawable.GradientDrawable;
import android.os.SystemClock;
import android.text.TextUtils;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.inputmethod.EditorInfo;
import android.widget.EditText;
import androidx.recyclerview.widget.ItemTouchHelper;
import org.telegram.ui.Components.ItemOptions;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.core.graphics.ColorUtils;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.MediaController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.R;
import org.telegram.messenger.SharedConfig;
import org.telegram.ui.ActionBar.BottomSheet;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.RecyclerListView;

import java.util.ArrayList;
import java.util.Locale;

public class PlayerQueueSheet extends BottomSheet implements NotificationCenter.NotificationCenterDelegate {

    private PlayerColors colors;
    private final GradientDrawable sheetBg = new GradientDrawable();
    private final int account;
    private final FrameLayout root;
    private final RecyclerListView list;
    private final LinearLayoutManager layoutManager;
    private final LinearLayout header;
    private final TextView title;
    private final TextView subtitle;
    private final TextView chip;
    private final GradientDrawable chipBg = new GradientDrawable();
    private final PlayerIcon chipIcon = PlayerIcon.stroke(PlayerIcon.SHUFFLE, 18);
    private final Adapter adapter = new Adapter();
    private boolean touchInList;
    private final EditText search;
    private final GradientDrawable searchBackground = new GradientDrawable();
    private final boolean focusSearch;
    private final ArrayList<MessageObject> allItems = new ArrayList<>();
    private ArrayList<MessageObject> visibleItems = new ArrayList<>();
    private final MusicQueueSearch queueSearch = new MusicQueueSearch();
    private long queueVersion;
    private int publicationGeneration;
    private boolean searchPending;
    private ArrayList<MessageObject> dragOriginal;
    private boolean dismissed;
    private ItemTouchHelper touchHelper;
    private final Runnable searchTask = () -> applySearch(true);

    public PlayerQueueSheet(Context context, PlayerColors colors, Theme.ResourcesProvider resourcesProvider, boolean focusSearch) {
        this(context, colors, resourcesProvider, focusSearch, "");
    }


    public PlayerQueueSheet(Context context, PlayerColors colors, Theme.ResourcesProvider resourcesProvider) {
        this(context, colors, resourcesProvider, false, "");
    }

    private PlayerQueueSheet(Context context, PlayerColors colors, Theme.ResourcesProvider resourcesProvider, boolean focusSearch, String query) {
        super(context, true, resourcesProvider);
        this.colors = colors;
        this.focusSearch = focusSearch;
        occupyNavigationBar = true;
        drawNavigationBar = false;
        setApplyTopPadding(false);
        setApplyBottomPadding(false);
        MessageObject playing = MediaController.getInstance().getPlayingMessageObject();
        account = playing != null ? playing.currentAccount : currentAccount;
        currentAccount = account;

        GradientDrawable bg = sheetBg;
        bg.setColor(colors.surfaceLow);
        bg.setCornerRadii(new float[]{dp(28), dp(28), dp(28), dp(28), 0, 0, 0, 0});
        root = new FrameLayout(context) {
            @Override
            protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
                int h = (int) (MeasureSpec.getSize(heightMeasureSpec) * 0.78f);
                if (header != null && list != null) {
                    header.measure(MeasureSpec.makeMeasureSpec(MeasureSpec.getSize(widthMeasureSpec), MeasureSpec.EXACTLY),
                            MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED));
                    int headerHeight = Math.max(dp(72), header.getMeasuredHeight());
                    header.getLayoutParams().height = headerHeight;
                    ((FrameLayout.LayoutParams) list.getLayoutParams()).topMargin = dp(42) + headerHeight;
                }
                super.onMeasure(widthMeasureSpec, MeasureSpec.makeMeasureSpec(h, MeasureSpec.EXACTLY));
            }

            @Override
            public boolean dispatchTouchEvent(MotionEvent ev) {
                int action = ev.getActionMasked();
                if (action == MotionEvent.ACTION_DOWN) {
                    touchInList = ev.getY() >= list.getTop();
                }
                boolean result = super.dispatchTouchEvent(ev);
                if ((action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) && touchInList) {
                    touchInList = false;
                    container.requestDisallowInterceptTouchEvent(false);
                }
                return result;
            }
        };
        root.setBackground(bg);
        containerView = root;

        View handle = new View(context);
        GradientDrawable handleBg = new GradientDrawable();
        handleBg.setCornerRadius(dp(2));
        handleBg.setColor(ColorUtils.setAlphaComponent(colors.onSurfaceVariant, 0x73));
        handle.setBackground(handleBg);
        root.addView(handle, LayoutHelper.createFrame(32, 4, Gravity.CENTER_HORIZONTAL | Gravity.TOP, 0, 18, 0, 0));

        header = new LinearLayout(context);
        header.setOrientation(LinearLayout.VERTICAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(24), 0, dp(24), 0);
        LinearLayout titles = new LinearLayout(context);
        titles.setOrientation(LinearLayout.VERTICAL);
        title = new TextView(context);
        title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 22);
        title.setTypeface(AndroidUtilities.bold());
        title.setTextColor(colors.onSurface);
        title.setText(getString(R.string.OEPlayerQueue));
        titles.addView(title, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT));
        subtitle = new TextView(context);
        subtitle.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        subtitle.setTextColor(colors.onSurfaceVariant);
        subtitle.setSingleLine(true);
        subtitle.setEllipsize(TextUtils.TruncateAt.END);
        titles.addView(subtitle, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, 0, 2, 0, 0));
        LinearLayout headingRow = new LinearLayout(context);
        headingRow.setGravity(Gravity.CENTER_VERTICAL);
        headingRow.addView(titles, LayoutHelper.createLinear(0, LayoutHelper.WRAP_CONTENT, 1f));
        chip = new TextView(context);
        chip.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        chip.setTypeface(AndroidUtilities.bold());
        chip.setGravity(Gravity.CENTER_VERTICAL);
        chip.setPadding(dp(12), 0, dp(16), 0);
        chip.setCompoundDrawablePadding(dp(8));
        chip.setCompoundDrawablesWithIntrinsicBounds(chipIcon, null, null, null);
        chip.setText(getString(R.string.OEPlayerShuffle));
        chip.setBackground(chipBg);
        chip.setOnClickListener(v -> {
            MediaController.getInstance().setPlaybackOrderType(SharedConfig.shuffleMusic ? 0 : 2);
            updateChip();
            refreshQueue();
            PlayerSheet.onModesChanged();
        });
        headingRow.addView(chip, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, 40, 12, 0, 0, 0));
        header.addView(headingRow, LayoutHelper.createLinear(-1, -2));
        search = new EditText(context);
        search.setSingleLine(true);search.setTextSize(16);search.setImeOptions(EditorInfo.IME_ACTION_SEARCH);
        search.setInputType(android.text.InputType.TYPE_CLASS_TEXT);
        search.setHint(getString(R.string.FlexyQueueSearch));search.setContentDescription(getString(R.string.FlexyQueueSearch));
        search.setTextColor(colors.onSurface);search.setHintTextColor(colors.onSurfaceVariant);
        searchBackground.setColor(colors.surfaceHigh);searchBackground.setCornerRadius(dp(24));
        search.setBackground(searchBackground);search.setPadding(dp(16),0,dp(16),0);
        search.setText(query);
        search.setOnEditorActionListener((view,action,event)->{
            if(action==EditorInfo.IME_ACTION_SEARCH){AndroidUtilities.cancelRunOnUIThread(searchTask);applySearch(true);AndroidUtilities.hideKeyboard(search);return true;}return false;
        });
        header.addView(search, LayoutHelper.createLinear(-1, 48, 0, 8, 0, 0));
        TextView hint = new TextView(context);hint.setTextSize(12);hint.setTextColor(colors.onSurfaceVariant);
        hint.setText(getString(R.string.FlexyQueueHint));header.addView(hint, LayoutHelper.createLinear(-1,-2,0,2,0,8));
        search.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence text,int start,int count,int after) { }
            public void onTextChanged(CharSequence text,int start,int before,int count) {
                publicationGeneration++;queueSearch.cancel();searchPending=true;
                AndroidUtilities.cancelRunOnUIThread(searchTask);AndroidUtilities.runOnUIThread(searchTask,120);
            }
            public void afterTextChanged(Editable text) { }
        });
        root.addView(header, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, 72, Gravity.TOP, 0, 34, 0, 0));

        list = new RecyclerListView(context) {
            @Override
            protected void onMeasure(int widthSpec, int heightSpec) {
                setPadding(dp(12), 0, dp(12), dp(24) + getBottomInset());
                super.onMeasure(widthSpec, heightSpec);
            }
        };
        layoutManager = new LinearLayoutManager(context);
        list.setLayoutManager(layoutManager);
        list.setAdapter(adapter);
        list.setClipToPadding(false);
        list.setVerticalScrollBarEnabled(false);
        list.setSelectorDrawableColor(0);
        list.setOnItemClickListener((view, position) -> onItemClick(position));
        list.addOnScrollListener(new RecyclerView.OnScrollListener() {
            @Override
            public void onScrolled(@NonNull RecyclerView recyclerView, int dx, int dy) {
                int last = layoutManager.findLastVisibleItemPosition();
                if (last >= adapter.getItemCount() - 5) {
                    MediaController.getInstance().loadMoreMusic();
                }
            }
        });
        root.addView(list, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.MATCH_PARENT, Gravity.TOP, 0, 34 + 72 + 8, 0, 0));

        touchHelper = new ItemTouchHelper(new ItemTouchHelper.SimpleCallback(ItemTouchHelper.UP | ItemTouchHelper.DOWN, 0) {
            @Override public boolean isLongPressDragEnabled(){return false;}
            @Override public int getMovementFlags(RecyclerView recycler, RecyclerView.ViewHolder holder) {
                int position=holder.getAdapterPosition();
                return searchPending || search.length()!=0 || position<0 || position>=visibleItems.size()
                        || MusicQueueOrder.same(visibleItems.get(position),MediaController.getInstance().getPlayingMessageObject())
                        ? 0 : super.getMovementFlags(recycler,holder);
            }
            @Override public void onSelectedChanged(RecyclerView.ViewHolder holder,int state) {
                if(state==ItemTouchHelper.ACTION_STATE_DRAG){publicationGeneration++;queueSearch.cancel();dragOriginal=new ArrayList<>(visibleItems);search.setEnabled(false);container.requestDisallowInterceptTouchEvent(true);}
                super.onSelectedChanged(holder,state);
            }
            @Override public boolean onMove(RecyclerView recycler,RecyclerView.ViewHolder from,RecyclerView.ViewHolder to) {
                int a=from.getAdapterPosition(),b=to.getAdapterPosition();
                if(a<0||b<0||a>=visibleItems.size()||b>=visibleItems.size()
                        ||MusicQueueOrder.same(visibleItems.get(b),MediaController.getInstance().getPlayingMessageObject()))return false;
                visibleItems.add(b,visibleItems.remove(a));adapter.notifyItemMoved(a,b);return true;
            }
            @Override public void clearView(RecyclerView recycler,RecyclerView.ViewHolder holder) {
                super.clearView(recycler,holder);
                ArrayList<MessageObject> expected=dragOriginal;search.setEnabled(true);container.requestDisallowInterceptTouchEvent(false);
                if(!dismissed&&expected!=null){
                    boolean ok;
                    try {ok=expected.equals(visibleItems)||MediaController.getInstance().reorderMusicQueue(new ArrayList<>(visibleItems),expected);}
                    finally {dragOriginal=null;}
                    if(!ok)android.widget.Toast.makeText(getContext(),getString(R.string.FlexyQueueEditFailed),android.widget.Toast.LENGTH_SHORT).show();
                    refreshQueue();
                }else dragOriginal=null;
            }
            @Override public void onSwiped(RecyclerView.ViewHolder holder,int direction) { }
        });
        touchHelper.attachToRecyclerView(list);
        list.setOnItemLongClickListener((view,position)->{if(position<0||position>=visibleItems.size())return false;showTrackMenu(view,visibleItems.get(position));return true;});
        updateChip();
        refreshQueue();
        int index = indexOfPlaying();
        if (index > 0) {
            layoutManager.scrollToPositionWithOffset(index, dp(72));
        }
        if(!focusSearch){root.setFocusableInTouchMode(true);root.requestFocus();}
    }

    @Override
    protected boolean canDismissWithSwipe() {
        return !touchInList || !list.canScrollVertically(-1);
    }

    @Override
    public void show() {
        super.show();
        if(focusSearch)search.post(()->{if(!dismissed){search.requestFocus();AndroidUtilities.showKeyboard(search);}});
        NotificationCenter nc = NotificationCenter.getInstance(account);
        nc.addObserver(this, NotificationCenter.messagePlayingDidStart);
        NotificationCenter.getGlobalInstance().addObserver(this, NotificationCenter.didSetNewTheme);
        nc.addObserver(this, NotificationCenter.messagePlayingPlayStateChanged);
        nc.addObserver(this, NotificationCenter.messagePlayingDidReset);
        nc.addObserver(this, NotificationCenter.moreMusicDidLoad);
        nc.addObserver(this, NotificationCenter.musicDidLoad);
        AndroidUtilities.setLightNavigationBar(this, ColorUtils.calculateLuminance(colors.surfaceLow) > 0.5);
    }

    @Override
    public void dismiss() {
        dismissed=true;
        publicationGeneration++;queueSearch.cancel();
        AndroidUtilities.cancelRunOnUIThread(searchTask);AndroidUtilities.hideKeyboard(search);
        if(touchHelper!=null)touchHelper.attachToRecyclerView(null);
        super.dismiss();
        NotificationCenter nc = NotificationCenter.getInstance(account);
        nc.removeObserver(this, NotificationCenter.messagePlayingDidStart);
        NotificationCenter.getGlobalInstance().removeObserver(this, NotificationCenter.didSetNewTheme);
        nc.removeObserver(this, NotificationCenter.messagePlayingPlayStateChanged);
        nc.removeObserver(this, NotificationCenter.messagePlayingDidReset);
        nc.removeObserver(this, NotificationCenter.moreMusicDidLoad);
        nc.removeObserver(this, NotificationCenter.musicDidLoad);
    }

    @Override
    public void didReceivedNotification(int id, int account, Object... args) {
        if (id == NotificationCenter.didSetNewTheme && org.telegram.messenger.BuildConfig.CONNECTED_ALPHA) {
            colors = PlayerColors.fromSignatureTheme(PlayerColors.isDark(resourcesProvider),resourcesProvider);
            search.setTextColor(colors.onSurface);search.setHintTextColor(colors.onSurfaceVariant);
            searchBackground.setColor(colors.surfaceHigh);
            sheetBg.setColor(colors.surfaceLow);
            title.setTextColor(colors.onSurface);
            subtitle.setTextColor(colors.onSurfaceVariant);
            updateChip();
            adapter.notifyDataSetChanged();
            return;
        }
        if (id == NotificationCenter.messagePlayingDidReset) {
            MessageObject mo = MediaController.getInstance().getPlayingMessageObject();
            if (mo == null || !mo.isMusic()) {
                dismiss();
                return;
            }
        }
        if (id == NotificationCenter.moreMusicDidLoad || id == NotificationCenter.musicDidLoad) {
            if(dragOriginal==null)refreshQueue();
            return;
        }
        if (id==NotificationCenter.messagePlayingDidStart && dragOriginal==null)refreshQueue();
        for (int i = 0; i < list.getChildCount(); i++) {
            View child = list.getChildAt(i);
            if (child instanceof Row) {
                ((Row) child).updateState();
            }
        }
    }

    private void updateChip() {
        boolean on = SharedConfig.shuffleMusic;
        chipBg.setCornerRadius(dp(on ? 12 : 20));
        chipBg.setColor(on ? colors.secondaryContainer : 0);
        chipBg.setStroke(on ? 0 : dp(1), colors.outlineVariant);
        int fg = on ? colors.onSecondaryContainer : colors.onSurfaceVariant;
        chip.setTextColor(fg);
        chipIcon.setColor(fg);
    }

    private void updateSubtitle() {
        int count = MediaController.getInstance().getPlaylist().size();
        subtitle.setText(LocaleController.formatPluralString("OEPlayerTracks", count));
    }

    private void refreshQueue() {
        if(dismissed||dragOriginal!=null)return;
        allItems.clear();allItems.addAll(MediaController.getInstance().getMusicQueueSnapshot());
        queueVersion++;
        applySearch(false);
    }
    private void applySearch(boolean userSearch) {
        if(dismissed||dragOriginal!=null)return;
        AndroidUtilities.cancelRunOnUIThread(searchTask);
        searchPending=true;
        final int ticket=++publicationGeneration;
        queueSearch.submit(allItems,queueVersion,visibleItems,search.getText().toString(),result -> {
            Runnable apply = () -> {
                if(dismissed||dragOriginal!=null||ticket!=publicationGeneration)return;
                searchPending=false;
                visibleItems=result.items;
                result.changes.dispatchUpdatesTo(adapter);
                subtitle.setText(visibleItems.isEmpty()?getString(R.string.FlexyQueueEmpty):LocaleController.formatPluralString("OEPlayerTracks",visibleItems.size()));
                for(int i=0;i<list.getChildCount();i++)if(list.getChildAt(i) instanceof Row)((Row)list.getChildAt(i)).updateState();
                if(userSearch)list.scrollToPosition(0);
            };
            if(list.isComputingLayout())list.post(apply);else apply.run();
        });
    }
    private MessageObject itemAt(int position) {return position>=0&&position<visibleItems.size()?visibleItems.get(position):null;}
    private MessageObject currentItem() {return MediaController.getInstance().getPlayingMessageObject();}
    private void showTrackMenu(View anchor,MessageObject item) {
        if(MusicQueueOrder.same(item,currentItem()))return;
        ItemOptions options=ItemOptions.makeOptions(container,colors.provider(resourcesProvider),anchor,true);
        MusicQueueActions.add(options,getContext(),item);
        if(!MusicQueueOrder.same(item,currentItem())){
            options.add(R.drawable.msg_delete,getString(R.string.FlexyQueueRemove),()->MediaController.getInstance().removeMusicFromQueue(item));
            int position=MusicQueueOrder.indexOf(allItems,item);
            if(search.length()==0&&position>0&&!MusicQueueOrder.same(allItems.get(position-1),currentItem())) {
                MessageObject previous=allItems.get(position-1);
                options.add(R.drawable.player_new_order,getString(R.string.FlexyQueueUp),()->MediaController.getInstance().moveMusicInQueue(item,previous));
            }
            if(search.length()==0&&position>=0&&position+1<allItems.size()&&!MusicQueueOrder.same(allItems.get(position+1),currentItem())) {
                MessageObject next=allItems.get(position+1);
                options.add(R.drawable.player_new_order,getString(R.string.FlexyQueueDown),()->MediaController.getInstance().moveMusicInQueue(item,next));
            }
        }
        options.show();
    }

    private int indexOfPlaying() {
        MessageObject playing = MediaController.getInstance().getPlayingMessageObject();
        int count = adapter.getItemCount();
        for (int i = 0; i < count; i++) {
            if (itemAt(i) == playing) {
                return i;
            }
        }
        return -1;
    }

    private void onItemClick(int position) {
        MessageObject mo = itemAt(position);
        if (mo == null) {
            return;
        }
        MediaController mc = MediaController.getInstance();
        if (mc.isPlayingMessage(mo)) {
            if (mc.isMessagePaused()) {
                mc.playMessage(mo);
            } else {
                mc.pauseMessage(mo);
            }
        } else {
            mc.findMessageInPlaylistAndPlay(mo);
        }
    }

    private class Adapter extends RecyclerListView.SelectionAdapter {

        @Override
        public boolean isEnabled(RecyclerView.ViewHolder holder) {
            return true;
        }

        @NonNull
        @Override
        public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            Row row = new Row(parent.getContext());
            row.setLayoutParams(new RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Math.max(dp(72), (int) Math.ceil(42 * getContext().getResources().getDisplayMetrics().scaledDensity + dp(20)))));
            return new RecyclerListView.Holder(row);
        }

        @Override
        public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position) {
            ((Row) holder.itemView).bind(itemAt(position));
        }

        @Override
        public int getItemCount() {
            return visibleItems.size();
        }
    }

    private class Row extends FrameLayout {

        private final CoverImage cover;
        private final TextView title;
        private final TextView artist;
        private final TextView duration;
        private final Equalizer equalizer;
        private final GradientDrawable bg = new GradientDrawable();
        private MessageObject message;

        Row(Context context) {
            super(context);
            bg.setCornerRadius(dp(20));
            setBackground(bg);
            setPadding(dp(10), 0, dp(14), 0);
            cover = new CoverImage(context, 22);
            cover.setRadius(dp(14));
            cover.setColors(colors.primaryContainer, colors.onPrimaryContainer);
            addView(cover, LayoutHelper.createFrame(52, 52, Gravity.LEFT | Gravity.CENTER_VERTICAL));
            LinearLayout texts = new LinearLayout(context);
            texts.setOrientation(LinearLayout.VERTICAL);
            title = new TextView(context);
            title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
            title.setTypeface(AndroidUtilities.bold());
            title.setSingleLine(true);
            title.setEllipsize(TextUtils.TruncateAt.END);
            texts.addView(title, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));
            artist = new TextView(context);
            artist.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
            artist.setSingleLine(true);
            artist.setEllipsize(TextUtils.TruncateAt.END);
            texts.addView(artist, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, 0, 2, 0, 0));
            addView(texts, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, Gravity.LEFT | Gravity.CENTER_VERTICAL, 66, 0, 88, 0));
            duration = new TextView(context);
            duration.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
            duration.setFontFeatureSettings("tnum");
            duration.setTextColor(colors.onSurfaceVariant);
            addView(duration, LayoutHelper.createFrame(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.RIGHT | Gravity.CENTER_VERTICAL,0,0,38,0));
            android.widget.ImageView handle=new android.widget.ImageView(context);handle.setScaleType(android.widget.ImageView.ScaleType.CENTER);
            PlayerIcon grip=PlayerIcon.stroke(PlayerIcon.QUEUE,20);grip.setColor(colors.onSurfaceVariant);handle.setImageDrawable(grip);
            handle.setContentDescription(getString(R.string.FlexyQueueReorder));
            addView(handle,LayoutHelper.createFrame(36,48,Gravity.RIGHT|Gravity.CENTER_VERTICAL));
            handle.setOnClickListener(v->{if(message!=null)showTrackMenu(handle,message);});
            handle.setOnTouchListener((v,event)->{
                if(event.getActionMasked()==MotionEvent.ACTION_DOWN&&!searchPending&&search.length()==0&&!MusicQueueOrder.same(message,currentItem())){
                    RecyclerView.ViewHolder holder=list.findContainingViewHolder(this);if(holder!=null){touchHelper.startDrag(holder);return true;}
                }return false;
            });
            equalizer = new Equalizer(context);
            addView(equalizer, LayoutHelper.createFrame(22,20,Gravity.RIGHT | Gravity.CENTER_VERTICAL,0,0,38,0));
        }

        void bind(MessageObject mo) {
            message = mo;
            if (mo == null) {
                return;
            }
            cover.setMessage(mo);
            title.setText(mo.getMusicTitle());
            artist.setText(mo.getMusicAuthor());
            int d = (int) Math.round(mo.getDuration());
            duration.setText(String.format(Locale.US, "%d:%02d", d / 60, d % 60));
            updateState();
        }

        void updateState() {
            boolean current = MusicQueueOrder.same(message, currentItem());
            bg.setColor(current ? colors.secondaryContainer : 0);
            bg.setStroke(current ? dp(1) : 0, colors.outlineVariant);
            title.setTextColor(current ? colors.onSecondaryContainer : colors.onSurface);
            artist.setTextColor(current ? colors.onSecondaryContainer : colors.onSurfaceVariant);
            duration.setVisibility(current ? GONE : VISIBLE);
            equalizer.setVisibility(current ? VISIBLE : GONE);
            equalizer.setPlaying(current && !MediaController.getInstance().isMessagePaused());
        }
    }

    private class Equalizer extends View {

        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final float[] still = {6, 11, 8};
        private final Runnable frame = this::invalidate;
        private final RectF rect = new RectF();
        private boolean playing;
        private float phase;
        private long lastFrame;

        Equalizer(Context context) {
            super(context);
            paint.setColor(colors.primary);
        }

        void setPlaying(boolean value) {
            if (playing != value) {
                playing = value;
                lastFrame = 0;
                invalidate();
            }
        }

        @Override protected void onDetachedFromWindow() {
            removeCallbacks(frame);
            lastFrame = 0;
            super.onDetachedFromWindow();
        }

        @Override
        protected void onDraw(@NonNull Canvas canvas) {
            paint.setColor(colors.primary);
            long now = SystemClock.elapsedRealtime();
            float dt = lastFrame == 0 ? 0.016f : Math.min(0.05f, (now - lastFrame) / 1000f);
            lastFrame = now;
            if (playing) {
                phase += 6f * dt;
            }

            float barW = dp(4);
            float gap = dp(3);
            float total = barW * 3 + gap * 2;
            float x = (getWidth() - total) / 2f;
            float bottom = getHeight();
            for (int k = 0; k < 3; k++) {
                float h = playing ? dp(5 + Math.abs((float) Math.sin(phase * 1.6f + k * 2.1f)) * 13) : dp(still[k]);
                rect.set(x, bottom - h, x + barW, bottom);
                canvas.drawRoundRect(rect, dp(2), dp(2), paint);
                x += barW + gap;
            }
            removeCallbacks(frame);
            if (playing && isShown() && getWindowVisibility() == VISIBLE && !org.telegram.messenger.LiteMode.isPowerSaverApplied()) {
                postDelayed(frame, 33);
            } else {
                lastFrame = 0;
            }
        }
    }
}
