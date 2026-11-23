package org.telegram.ui.Components.Reactions;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;

import androidx.annotation.NonNull;
import androidx.core.math.MathUtils;
import androidx.recyclerview.widget.RecyclerView;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.MessageObject;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.Cells.ChatMessageCell;
import org.telegram.ui.ChatActivity;
import org.telegram.ui.Components.CubicBezierInterpolator;
import org.telegram.ui.Components.FragmentContextView;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.ReactionsContainerLayout;
import org.telegram.ui.Components.RecyclerListView;

import java.util.Collections;
import java.util.List;

public class ChatSelectionReactionMenuOverlay extends FrameLayout {
    private ChatActivity parentFragment;
    private ReactionsContainerLayout reactionsContainerLayout;

    private List<MessageObject> selectedMessages = Collections.emptyList();
    private boolean isVisible;
    private MessageObject currentPrimaryObject;

    private int mPadding = 22;
    private int mSidePadding = 24;

    private float currentOffsetY;
    private float toOffsetY;
    private float translationOffsetY;
    private long lastUpdate;
    private boolean hiddenByScroll;
    private boolean positionFramePending;
    private ValueAnimator hideAnimator;
    private final Runnable positionFrame = () -> {
        positionFramePending = false;
        invalidatePosition();
    };
    private final Runnable showMenu = this::showSelectedMessageMenu;

    private boolean messageSet;

    public ChatSelectionReactionMenuOverlay(ChatActivity fragment, Context context) {
        super(context);
        setVisibility(GONE);

        this.parentFragment = fragment;

        setClipToPadding(false);
        setClipChildren(false);

        fragment.getChatListView().addOnScrollListener(new RecyclerView.OnScrollListener() {
            @Override
            public void onScrolled(@NonNull RecyclerView recyclerView, int dx, int dy) {
                if (isVisible()) schedulePositionFrame();
            }
        });
    }

    private void checkCreateReactionsLayout() {
        if (reactionsContainerLayout == null) {
            final boolean tags = parentFragment.getUserConfig().getClientUserId() == parentFragment.getDialogId();

            reactionsContainerLayout = new ReactionsContainerLayout(tags ? ReactionsContainerLayout.TYPE_TAGS : ReactionsContainerLayout.TYPE_DEFAULT, parentFragment, getContext(), parentFragment.getCurrentAccount(), parentFragment.getResourceProvider()) {
                float enabledAlpha = 1f;
                long lastUpdate;

                {
                    setWillNotDraw(false);
                }

                @Override
                public void draw(Canvas canvas) {
                    final long now = SystemClock.uptimeMillis();
                    final long dt = lastUpdate == 0 ? 0 : now - lastUpdate;
                    lastUpdate = now;
                    if (enabledAlpha == 1f) {
                        super.draw(canvas);
                    } else if (enabledAlpha > 0f) {
                        final int save = canvas.saveLayerAlpha(0, 0, getWidth(), getHeight(), (int) (0xFF * enabledAlpha));
                        super.draw(canvas);
                        canvas.restoreToCount(save);
                    }

                    if (!isEnabled() && enabledAlpha != 0f) {
                        enabledAlpha = Math.max(0, enabledAlpha - dt / 150f);
                        invalidate();

                        if (enabledAlpha == 0) {
                            setVisibility(GONE);
                        }
                    } else if (isEnabled() && enabledAlpha != 1f) {
                        enabledAlpha = Math.min(1, enabledAlpha + dt / 150f);
                        invalidate();
                    }
                }

                @Override
                public void setEnabled(boolean enabled) {
                    if (isEnabled() != enabled) lastUpdate = SystemClock.uptimeMillis();
                    super.setEnabled(enabled);
                }

                @Override
                public void setVisibility(int visibility) {
                    super.setVisibility(visibility);

                    if (visibility == View.GONE && enabledAlpha != 0) {
                        enabledAlpha = 0;
                    }
                }
            };
            reactionsContainerLayout.setPadding(AndroidUtilities.dp(4) + (LocaleController.isRTL ? 0 : mSidePadding), AndroidUtilities.dp(4), AndroidUtilities.dp(4) + (LocaleController.isRTL ? mSidePadding : 0), AndroidUtilities.dp(mPadding));
            reactionsContainerLayout.setDelegate(new ReactionsContainerLayout.ReactionsContainerDelegate() {
                @Override
                public void onReactionClicked(View view, ReactionsLayoutInBubble.VisibleReaction visibleReaction, boolean longpress, boolean addToRecent) {
                    final MessageObject message = currentPrimaryObject;
                    final ReactionsContainerLayout menu = reactionsContainerLayout;
                    parentFragment.selectReaction(null, message, menu, view, 0, 0, visibleReaction, false, longpress, addToRecent, false);
                    AndroidUtilities.runOnUIThread(() -> {
                        if (menu == null || menu != reactionsContainerLayout || message != currentPrimaryObject) return;
                        menu.dismissParent(true);
                        hideMenu();
                    });
                }

                @Override
                public void hideMenu() {
                    parentFragment.clearSelectionMode(true);
                }
            });
            reactionsContainerLayout.setClipChildren(false);
            reactionsContainerLayout.setClipToPadding(false);
            addView(reactionsContainerLayout, LayoutHelper.createFrame(LayoutHelper.WRAP_CONTENT, 70 + mPadding, Gravity.RIGHT));
        }
    }

    public boolean isVisible() {
        return isVisible && !hiddenByScroll;
    }

    public void invalidatePosition() {
        invalidatePosition(true);
    }

    private int[] pos = new int[2];
    public void invalidatePosition(boolean animate) {
        if (!isVisible() || currentPrimaryObject == null || reactionsContainerLayout == null) {
            return;
        }
        final long now = SystemClock.uptimeMillis();
        final long dt = lastUpdate == 0 ? 0 : now - lastUpdate;
        final boolean offsetWasAnimating = currentOffsetY != toOffsetY;
        lastUpdate = now;

        RecyclerListView listView = parentFragment.getChatListView();
        for (int i = 0; i < listView.getChildCount(); i++) {
            View ch = listView.getChildAt(i);
            if (ch instanceof ChatMessageCell) {
                ChatMessageCell cell = (ChatMessageCell) ch;

                MessageObject obj = cell.getMessageObject();
                if (obj != null && obj.getId() == currentPrimaryObject.getId()
                        && obj.getDialogId() == currentPrimaryObject.getDialogId()) {
                    listView.getLocationInWindow(pos);
                    final float listY = pos[1];
                    getLocationInWindow(pos);
                    final float offsetY = listY - pos[1] - parentFragment.getPullingDownOffset();
                    boolean mirrorX = obj.isOutOwner();
                    if (reactionsContainerLayout != null) {
                        reactionsContainerLayout.setMirrorX(mirrorX);
                        reactionsContainerLayout.setPadding(AndroidUtilities.dp(4) + (LocaleController.isRTL || mirrorX ? 0 : mSidePadding), AndroidUtilities.dp(mPadding), AndroidUtilities.dp(4) + (LocaleController.isRTL || mirrorX ? mSidePadding : 0), AndroidUtilities.dp(mPadding));
                    }
                    int height = getHeight() != 0 ? getHeight() : listView.getHeight();
                    int groupHeight;

                    final MessageObject.GroupedMessages group = cell.getCurrentMessagesGroup();
                    if (group != null) {
                        groupHeight = group.transitionParams.bottom - group.transitionParams.top;
                    } else {
                        groupHeight = cell.getHeight();
                    }

                    float y = cell.getY() + offsetY - AndroidUtilities.dp(74);
                    float min = AndroidUtilities.dp(14), max = height - AndroidUtilities.dp(218);
                    FragmentContextView fragmentContextView = parentFragment.getFragmentContextView();
                    if (fragmentContextView != null && fragmentContextView.getVisibility() == View.VISIBLE) {
                        min += fragmentContextView.getHeight();
                    }
                    boolean newVisibleOffset;
                    boolean flippedVertically;
                    if (y > min - groupHeight / 2f && y < max) {
                        newVisibleOffset = true;
                        flippedVertically = false;
                        toOffsetY = 0f;
                    } else if (y < min - groupHeight - AndroidUtilities.dp(92) || y > max) {
                        newVisibleOffset = false;
                        flippedVertically = false;
                    } else {
                        newVisibleOffset = true;
                        translationOffsetY = groupHeight + AndroidUtilities.dp(56);
                        flippedVertically = true;
                        toOffsetY = 1f;
                    }
                    if (!animate) {
                        currentOffsetY = toOffsetY;
                    } else if (offsetWasAnimating && currentOffsetY != toOffsetY) {
                        final float step = dt / 220f;
                        currentOffsetY = toOffsetY > currentOffsetY ? Math.min(currentOffsetY + step, toOffsetY)
                                : Math.max(currentOffsetY - step, toOffsetY);
                    }

                    y += CubicBezierInterpolator.DEFAULT.getInterpolation(currentOffsetY) * translationOffsetY;
                    if (reactionsContainerLayout == null) {
                        return;
                    }
                    if (flippedVertically != reactionsContainerLayout.isFlippedVertically()) {
                        reactionsContainerLayout.setFlippedVertically(flippedVertically);
                    }
                    if (newVisibleOffset && currentOffsetY != toOffsetY) {
                        schedulePositionFrame();
                    }
                    if (newVisibleOffset != reactionsContainerLayout.isEnabled()) {
                        reactionsContainerLayout.setEnabled(newVisibleOffset);
                        reactionsContainerLayout.invalidate();
                        if (newVisibleOffset) {
                            reactionsContainerLayout.setVisibility(VISIBLE);
                            if (!messageSet) {
                                messageSet = true;
                                reactionsContainerLayout.setMessage(currentPrimaryObject, parentFragment.getCurrentChatInfo(), true);
                            }
                        }
                    }
                    reactionsContainerLayout.setTranslationY(MathUtils.clamp(y, min, max));
                    final float cellTranslationX = cell.getNonAnimationTranslationX(true);
                    reactionsContainerLayout.setTranslationX(cellTranslationX);

                    boolean invalidate = false;
                    LayoutParams params = (LayoutParams) reactionsContainerLayout.getLayoutParams();
                    int left = Math.max(0, cell.getBackgroundDrawableLeft() - AndroidUtilities.dp(32));
                    int right = Math.max((int) cellTranslationX, cell.getWidth() - cell.getBackgroundDrawableRight() - AndroidUtilities.dp(32));

                    int minWidth = AndroidUtilities.dp(40) * 8;
                    if (getWidth() - right - left < minWidth) {
                        if (mirrorX) {
                            right = 0;
                            left = Math.min(left, getWidth() - right - minWidth);
                        } else {
                            left = 0;
                            right = Math.min(right, getWidth() - left - minWidth);
                        }
                    }

                    int gravity = mirrorX ? Gravity.RIGHT : Gravity.LEFT;
                    if (gravity != params.gravity) {
                        params.gravity = gravity;
                        invalidate = true;
                    }
                    if (left != params.leftMargin) {
                        params.leftMargin = left;
                        invalidate = true;
                    }
                    if (right != params.rightMargin) {
                        params.rightMargin = right;
                        invalidate = true;
                    }
                    if (invalidate) {
                        reactionsContainerLayout.requestLayout();
                    }
                    return;
                }
            }
        }

        if (reactionsContainerLayout != null && reactionsContainerLayout.isEnabled()) {
            reactionsContainerLayout.setEnabled(false);
        }
    }

    private void schedulePositionFrame() {
        if (!positionFramePending && isAttachedToWindow()) {
            positionFramePending = true;
            postOnAnimation(positionFrame);
        }
    }

    private MessageObject findPrimaryObject() {
        if (isVisible && !selectedMessages.isEmpty()) {
            MessageObject msg = selectedMessages.get(0);

            if (msg.getGroupId() != 0) {
                MessageObject.GroupedMessages groupedMessages = parentFragment.getGroup(msg.getGroupId());
                if (groupedMessages != null && groupedMessages.messages != null) {
                    for (MessageObject obj : groupedMessages.messages) {
                        if (obj.messageOwner != null && obj.messageOwner.reactions != null && obj.messageOwner.reactions.results != null &&
                                !obj.messageOwner.reactions.results.isEmpty()) {
                            return obj;
                        }
                    }
                }
            }

            return msg;
        }
        return null;
    }

    private boolean isMessageTypeAllowed(MessageObject obj) {
        if (obj != null && obj.messageOwner != null && obj.messageOwner.rich_message != null) return true;
        return obj != null && !obj.needDrawBluredPreview() && (
            MessageObject.isPhoto(obj.messageOwner) && MessageObject.getMedia(obj.messageOwner).webpage == null ||
            obj.getDocument() != null && (
                MessageObject.isVideoDocument(obj.getDocument()) ||
                MessageObject.isGifDocument(obj.getDocument())
            )
        );
    }

    public void setSelectedMessages(List<MessageObject> messages) {
        this.selectedMessages = messages;

        boolean visible = false;

        if (parentFragment.getChatMode() == ChatActivity.MODE_SCHEDULED || parentFragment.getChatMode() == ChatActivity.MODE_QUICK_REPLIES || parentFragment.getChatMode() == ChatActivity.MODE_EDIT_BUSINESS_LINK || parentFragment.isReport() || parentFragment.isSecretChat() || parentFragment.getCurrentChatInfo() != null && parentFragment.getCurrentChatInfo().available_reactions instanceof TLRPC.TL_chatReactionsNone) {
            visible = false;
        } else if (!messages.isEmpty()) {
            visible = true;

            boolean hasGroupId = false;
            long groupId = 0;
            for (MessageObject obj : messages) {
                if (!isMessageTypeAllowed(obj)) {
                    visible = false;
                    break;
                }
                if (!hasGroupId) {
                    hasGroupId = true;
                    groupId = obj.getGroupId();
                } else if (groupId != obj.getGroupId() || groupId == 0) {
                    visible = false;
                    break;
                }
            }
        }

        if (visible != isVisible) {
            isVisible = visible;
            hiddenByScroll = false;
            animateVisible(visible);
        } else if (visible) {
            currentPrimaryObject = findPrimaryObject();
        }
    }

    private void animateVisible(boolean visible) {
        cancelMenuTransition();
        if (visible) {
            setVisibility(VISIBLE);
            post(showMenu);
        } else {
            messageSet = false;
            if (reactionsContainerLayout == null || !isAttachedToWindow()) {
                clearMenu();
                return;
            }
            ValueAnimator animator = hideAnimator = ValueAnimator.ofFloat(reactionsContainerLayout.getAlpha(), 0).setDuration(150);
            animator.addUpdateListener(animation -> {
                float val = (float) animation.getAnimatedValue();
                if (reactionsContainerLayout != null) {
                    reactionsContainerLayout.setAlpha(val);
                }
            });
            animator.addListener(new AnimatorListenerAdapter() {
                @Override
                public void onAnimationEnd(Animator animation) {
                    hideAnimator = null;
                    clearMenu();
                }
            });
            animator.start();
        }
    }

    private void showSelectedMessageMenu() {
        if (!isVisible() || !isAttachedToWindow()) return;
        currentPrimaryObject = findPrimaryObject();
        if (currentPrimaryObject == null) return;
        checkCreateReactionsLayout();
        reactionsContainerLayout.setAlpha(1f);
        invalidatePosition(false);
        if (reactionsContainerLayout.isEnabled()) {
            if (!messageSet) {
                messageSet = true;
                reactionsContainerLayout.setMessage(currentPrimaryObject, parentFragment.getCurrentChatInfo(), true);
            }
            reactionsContainerLayout.startEnterAnimation(false);
        } else {
            messageSet = false;
            reactionsContainerLayout.setTransitionProgress(1f);
        }
    }

    private void cancelMenuTransition() {
        removeCallbacks(showMenu);
        removeCallbacks(positionFrame);
        positionFramePending = false;
        lastUpdate = 0;
        if (hideAnimator != null) {
            hideAnimator.removeAllListeners();
            hideAnimator.cancel();
            hideAnimator = null;
        }
    }

    private void clearMenu() {
        setVisibility(GONE);
        if (reactionsContainerLayout != null) {
            final CustomEmojiReactionsWindow window = reactionsContainerLayout.getReactionsWindow();
            if (window != null) window.dismiss(false);
            removeView(reactionsContainerLayout);
            reactionsContainerLayout = null;
        }
        currentPrimaryObject = null;
        messageSet = false;
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        if (isVisible()) animateVisible(true);
    }

    @Override
    protected void onDetachedFromWindow() {
        cancelMenuTransition();
        clearMenu();
        super.onDetachedFromWindow();
    }

    public boolean onBackPressed(boolean invoked) {
        if (reactionsContainerLayout != null && reactionsContainerLayout.getReactionsWindow() != null) {
            if (invoked) reactionsContainerLayout.dismissWindow();
            return false;
        }
        return true;
    }

    public void setHiddenByScroll(boolean hiddenByScroll) {
        if (this.hiddenByScroll == hiddenByScroll) return;
        this.hiddenByScroll = hiddenByScroll;

        if (isVisible) animateVisible(!hiddenByScroll);
    }
}
