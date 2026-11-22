package app.flexygram.notifications;

import static org.telegram.messenger.AndroidUtilities.dp;

import android.content.Context;
import android.content.SharedPreferences;
import android.text.TextUtils;
import android.view.HapticFeedbackConstants;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;

import org.telegram.messenger.ChatObject;
import org.telegram.messenger.DialogObject;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.R;
import org.telegram.messenger.SharedConfig;
import org.telegram.messenger.UserConfig;
import org.telegram.messenger.UserObject;
import org.telegram.messenger.voip.VoIPService;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ChatActivity;
import org.telegram.ui.LaunchActivity;

import java.util.List;

public final class InAppAlerts {
    private static final int ENABLED = 1;
    private static final int IMPORTANT_ONLY = 1 << 1;
    private static final int NAME_ONLY = 1 << 2;
    private static final int HIDDEN = 1 << 3;
    private static final int VIBRATE = 1 << 4;
    private static final int TOPIC_DISABLED = 1 << 5;
    private static final String ACTIVE_COUNT = "flexy_alert_active_count";

    private final LaunchActivity activity;
    private final FrameLayout root;
    private final SharedPreferences preferences;
    private InAppBannerView banner;
    private long shownDialog, shownTopic;
    private int shownCount, newestId;

    public InAppAlerts(LaunchActivity activity, FrameLayout root, SharedPreferences preferences) {
        this.activity = activity;
        this.root = root;
        this.preferences = preferences;
    }

    public static SharedPreferences preferences(int account) {
        return MessagesController.getNotificationsSettings(account);
    }

    public static boolean hasSelections(SharedPreferences preferences) {
        return preferences.getInt(ACTIVE_COUNT, 0) > 0;
    }

    private static void saveOptions(SharedPreferences preferences, long dialog, long topic, int options) {
        String key = key(dialog, topic);
        boolean wasEnabled = (preferences.getInt(key, 0) & ENABLED) != 0;
        boolean enabled = (options & ENABLED) != 0;
        SharedPreferences.Editor editor = preferences.edit();
        if (options == 0) editor.remove(key);
        else editor.putInt(key, options);
        if (wasEnabled != enabled) {
            int change = enabled ? 1 : -1;
            editor.putInt(ACTIVE_COUNT, Math.max(0, preferences.getInt(ACTIVE_COUNT, 0) + change));
            if (topic != 0) {
                String topicCount = topicCountKey(dialog);
                int count = preferences.getInt(topicCount, 0) + change;
                if (count > 0) editor.putInt(topicCount, count);
                else editor.remove(topicCount);
            }
        }
        editor.apply();
    }

    private static String key(long dialog, long topic) {
        return "flexy_alert:" + dialog + ":" + topic;
    }

    private static String topicCountKey(long dialog) {
        return "flexy_alert_topics:" + dialog;
    }

    public static void showSettings(Context context, int account, long dialog, long topic) {
        SharedPreferences preferences = preferences(account);
        String key = key(dialog, topic);
        int current = preferences.getInt(key, 0);
        int inherited = topic == 0 ? 0 : preferences.getInt(key(dialog, 0), 0);
        int selected = current == 0 ? inherited : current;
        String[] labels = {
                LocaleController.getString(R.string.FlexyInAppAlertEnabled),
                LocaleController.getString(R.string.FlexyInAppAlertImportant),
                LocaleController.getString(R.string.FlexyInAppAlertNames),
                LocaleController.getString(R.string.FlexyInAppAlertPrivate),
                LocaleController.getString(R.string.FlexyInAppAlertVibrate)
        };
        int[] flags = {ENABLED, IMPORTANT_ONLY, NAME_ONLY, HIDDEN, VIBRATE};
        boolean[] values = new boolean[flags.length];
        for (int i = 0; i < flags.length; i++) values[i] = (selected & flags[i]) != 0;
        ScrollView scroll = new ScrollView(context);
        LinearLayout rows = new LinearLayout(context);
        rows.setOrientation(LinearLayout.VERTICAL);
        int padding = dp(20);
        rows.setPadding(padding, 0, padding, 0);
        scroll.addView(rows);
        CheckBox[] items = new CheckBox[flags.length];
        for (int i = 0; i < flags.length; i++) {
            int index = i;
            CheckBox item = new CheckBox(context);
            item.setText(labels[i]);
            item.setTextColor(Theme.getColor(Theme.key_dialogTextBlack));
            item.setMinHeight(dp(48));
            item.setChecked(values[i]);
            items[i] = item;
            item.setOnCheckedChangeListener((button, checked) -> {
                values[index] = checked;
                if (checked && index == 2) items[3].setChecked(false);
                if (checked && index == 3) items[2].setChecked(false);
            });
            rows.addView(item);
        }
        AlertDialog.Builder builder = new AlertDialog.Builder(context)
                .setTitle(LocaleController.getString(R.string.FlexyInAppAlertTitle))
                .setView(scroll)
                .setPositiveButton(LocaleController.getString(R.string.Save), (dialogInterface, which) -> {
                    int updated = 0;
                    for (int i = 0; i < flags.length; i++) {
                        if (values[i]) updated |= flags[i];
                    }
                    if ((updated & ENABLED) == 0) updated = topic == 0 ? 0 : TOPIC_DISABLED;
                    saveOptions(preferences, dialog, topic, updated);
                })
                .setNegativeButton(LocaleController.getString(R.string.Cancel), null);
        if (topic != 0) {
            builder.setNeutralButton(LocaleController.getString(R.string.FlexyInAppAlertInherit),
                    (d, which) -> saveOptions(preferences, dialog, topic, 0));
        }
        LaunchActivity launch = LaunchActivity.instance;
        if (launch != null) {
            Button previewButton = new Button(context);
            previewButton.setText(LocaleController.getString(R.string.FlexyInAppAlertTest));
            previewButton.setAllCaps(false);
            rows.addView(previewButton);
            AlertDialog settings = builder.create();
            previewButton.setOnClickListener(v -> {
                settings.dismiss();
                launch.previewFlexyInAppAlert(account);
            });
            settings.show();
        } else {
            builder.show();
        }
    }

    public void onMessages(int account, long dialog, List<MessageObject> messages, ChatActivity visibleChat) {
        if (dialog == 0 || DialogObject.isEncryptedDialog(dialog) || SharedConfig.appLocked
                || SharedConfig.isWaitingForPasscodeEnter || VoIPService.getSharedInstance() != null) return;
        int dialogFlags = preferences.getInt(key(dialog, 0), 0);
        if ((dialogFlags & ENABLED) == 0 && (dialog > 0 || preferences.getInt(topicCountKey(dialog), 0) == 0)) return;
        MessagesController controller = MessagesController.getInstance(account);
        TLRPC.Chat chat = dialog < 0 ? controller.getChat(-dialog) : null;
        boolean forum = ChatObject.isForum(chat);
        if ((dialogFlags & ENABLED) == 0 && !forum) return;

        long visibleTopic = -1;
        if (visibleChat != null && visibleChat.getDialogId() == dialog) {
            visibleTopic = visibleChat.getTopicId();
            if (visibleTopic == 0) return;
        }
        boolean sameDialogShowing = banner != null && banner.isShowing() && shownDialog == dialog;
        if (banner != null && banner.isInteracting() && !sameDialogShowing) return;
        MessageObject newest = null;
        long topic = 0;
        int count = 0, flags = 0;
        for (int i = messages.size() - 1; i >= 0; i--) {
            MessageObject message = messages.get(i);
            if (message.messageOwner == null || message.getId() <= 0 || message.isOut() || !message.isUnread()
                    || message.messageOwner instanceof TLRPC.TL_messageService || message.isEphemeralAndNotWelcome()) continue;
            long messageTopic = forum ? message.getTopicId() : 0;
            if (messageTopic == visibleTopic || (newest != null && topic != messageTopic)) continue;
            if (sameDialogShowing && shownTopic == messageTopic
                    && message.getId() <= newestId) continue;
            int options = newest != null ? flags : messageTopic == 0 ? dialogFlags
                    : preferences.getInt(key(dialog, messageTopic), dialogFlags);
            if ((options & ENABLED) == 0) continue;
            if ((options & IMPORTANT_ONLY) != 0 && !message.messageOwner.mentioned
                    && (message.replyMessageObject == null || !message.replyMessageObject.isOut())) continue;
            if (newest == null) {
                newest = message;
                topic = messageTopic;
                flags = options;
            }
            count++;
        }
        if (newest == null) return;
        boolean update = sameDialogShowing && shownTopic == topic;
        if (!update && banner != null && banner.isInteracting()) return;
        int id = newest.getId();
        shownDialog = dialog;
        shownTopic = topic;
        newestId = id;
        shownCount = update ? Math.min(999, shownCount + count) : Math.min(999, count);

        String generic = LocaleController.getString(R.string.FlexyInAppAlertNewMessage);
        CharSequence name = generic;
        CharSequence preview = null;
        if ((flags & HIDDEN) == 0) {
            TLRPC.User user = dialog > 0 ? controller.getUser(dialog) : null;
            name = chat != null ? chat.title : user != null ? UserObject.getUserName(user) : generic;
            if (forum && topic != 0) {
                TLRPC.TL_forumTopic forumTopic = controller.getTopicsController().findTopic(-dialog, topic);
                if (forumTopic != null && !TextUtils.isEmpty(forumTopic.title)) {
                    name = TextUtils.concat(name, " · ", forumTopic.title);
                }
            }
            if ((flags & NAME_ONLY) == 0) {
                if (shownCount > 1) {
                    preview = LocaleController.formatPluralString("NewMessages", shownCount);
                } else {
                    preview = canPreview(controller, dialog, newest)
                            ? newest.messageOwner.message.subSequence(0, Math.min(180, newest.messageOwner.message.length()))
                            : generic;
                }
            }
        }
        prepareBanner();
        banner.show(name, preview, () -> {
            if (UserConfig.selectedAccount == account && activity.canShowFlexyInAppAlert()) {
                activity.openMessage(dialog, id, null, null, 0, -1, null);
            }
        }, update);
        if (!update && (flags & VIBRATE) != 0) root.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
    }

    private void prepareBanner() {
        if (banner == null) {
            banner = new InAppBannerView(activity);
            root.addView(banner, new FrameLayout.LayoutParams(-1, -1));
        }
        if (root.getChildAt(root.getChildCount() - 1) != banner) banner.bringToFront();
    }

    public void preview() {
        shownDialog = 0;
        prepareBanner();
        banner.show(LocaleController.getString(R.string.FlexyInAppAlertTitle),
                LocaleController.getString(R.string.FlexyInAppAlertTestMessage), null, false);
    }

    private static boolean canPreview(MessagesController controller, long dialog, MessageObject message) {
        TLRPC.Message owner = message.messageOwner;
        if (message.isSecretMedia() || UserObject.isService(dialog) || owner.noforwards || controller.isPeerNoForwards(dialog)
                || TextUtils.isEmpty(owner.message)) return false;
        if (owner.entities == null) return true;
        for (TLRPC.MessageEntity entity : owner.entities) {
            if (entity instanceof TLRPC.TL_messageEntitySpoiler) return false;
        }
        return true;
    }

    public void hide() {
        if (banner != null) banner.hide();
    }

    public void dispose() {
        hide();
        if (banner != null) root.removeView(banner);
    }
}
