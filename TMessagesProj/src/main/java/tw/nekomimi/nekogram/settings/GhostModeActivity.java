package tw.nekomimi.nekogram.settings;

import static org.telegram.messenger.LocaleController.getString;
import static org.telegram.ui.LaunchActivity.getLastFragment;

import android.content.Context;
import android.util.TypedValue;
import android.view.View;
import android.widget.LinearLayout;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.radolyn.ayugram.utils.AyuState;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.R;
import org.telegram.messenger.UserConfig;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.CheckBoxCell;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextCheckCell2;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.AlertsCreator;
import org.telegram.ui.Components.BulletinFactory;
import org.telegram.ui.Components.EditTextBoldCursor;
import org.telegram.ui.Components.LayoutHelper;

import java.util.Locale;

import tw.nekomimi.nekogram.NekoConfig;
import tw.nekomimi.nekogram.config.ConfigItem;
import tw.nekomimi.nekogram.ui.cells.HeaderCell;
import xyz.nextalone.nagram.NaConfig;

public class GhostModeActivity extends BaseNekoSettingsActivity {

    private static final int[] OFFLINE_DELAYS = {0, 500, 1000, 3000, 5000};

    private int ghostEssentialsHeaderRow;
    private int ghostModeToggleRow;
    private int ghostPresetRow;

    private int sendReadMessagePacketsRow;
    private int sendReadStoriesPacketsRow;
    private int sendOnlinePacketsRow;
    private int sendUploadProgressRow;
    private int sendOfflinePacketAfterOnlineRow;
    private int ghostModeNoticeRow;

    private int ghostAdvancedHeaderRow;
    private int blockMentionsReadRow;
    private int blockReactionOnlineRow;
    private int offlineDelayRow;
    private int markReadAfterSendRow;
    private int markReadAfterSendNoticeRow;

    private int sendWithoutSoundRow;
    private int sendWithoutSoundNoticeRow;
    private int scheduledSendRow;
    private int scheduledSendNoticeRow;
    private int showGhostInDrawerRow;
    private int showGhostModeStatusRow;
    private int ghostEndDividerRow;

    private int deletedHeaderRow;
    private int keepDeletedRow;
    private int translucentDeletedRow;
    private int deletedIconRow;
    private int customDeletedMarkRow;
    private int deletedNoticeRow;

    private boolean ghostModeMenuExpanded;

    @Override
    protected void updateRows() {
        super.updateRows();

        ghostEssentialsHeaderRow = addRow();
        ghostModeToggleRow = addRow();
        if (ghostModeMenuExpanded) {
            sendReadMessagePacketsRow = addRow();
            sendReadStoriesPacketsRow = addRow();
            sendOnlinePacketsRow = addRow();
            sendUploadProgressRow = addRow();
            sendOfflinePacketAfterOnlineRow = addRow();
            ghostModeNoticeRow = addRow();
        } else {
            sendReadMessagePacketsRow = -1;
            sendReadStoriesPacketsRow = -1;
            sendOnlinePacketsRow = -1;
            sendUploadProgressRow = -1;
            sendOfflinePacketAfterOnlineRow = -1;
            ghostModeNoticeRow = -1;
        }
        ghostPresetRow = addRow();

        ghostAdvancedHeaderRow = addRow();
        blockMentionsReadRow = addRow();
        blockReactionOnlineRow = addRow();
        offlineDelayRow = addRow();
        markReadAfterSendRow = addRow();
        markReadAfterSendNoticeRow = addRow();
        sendWithoutSoundRow = addRow();
        sendWithoutSoundNoticeRow = addRow();
        scheduledSendRow = addRow();
        scheduledSendNoticeRow = addRow();
        showGhostInDrawerRow = addRow();
        showGhostModeStatusRow = addRow();
        ghostEndDividerRow = addRow();

        deletedHeaderRow = addRow();
        keepDeletedRow = addRow();
        final boolean keepDeleted = NaConfig.INSTANCE.getEnableSaveDeletedMessages().Bool();
        if (keepDeleted) {
            translucentDeletedRow = addRow();
            deletedIconRow = addRow();
            customDeletedMarkRow = NaConfig.INSTANCE.getUseDeletedIcon().Bool() ? -1 : addRow();
        } else {
            translucentDeletedRow = -1;
            deletedIconRow = -1;
            customDeletedMarkRow = -1;
        }
        deletedNoticeRow = addRow();
    }

    @Override
    public boolean onFragmentCreate() {
        super.onFragmentCreate();
        return true;
    }

    @Override
    public void onFragmentDestroy() {
        super.onFragmentDestroy();
    }

    private void notifyRowIfVisible(int row, Object payload) {
        if (listAdapter != null && row >= 0) {
            listAdapter.notifyItemChanged(row, payload);
        }
    }

    private void updateGhostViews() {
        var isActive = NekoConfig.isGhostModeActive();

        notifyRowIfVisible(ghostModeToggleRow, PARTIAL);
        notifyRowIfVisible(ghostPresetRow, PARTIAL);
        notifyRowIfVisible(sendReadMessagePacketsRow, !isActive);
        notifyRowIfVisible(sendOnlinePacketsRow, !isActive);
        notifyRowIfVisible(sendUploadProgressRow, !isActive);
        notifyRowIfVisible(sendReadStoriesPacketsRow, !isActive);
        notifyRowIfVisible(sendOfflinePacketAfterOnlineRow, isActive);
        notifyRowIfVisible(blockMentionsReadRow, PARTIAL);
        notifyRowIfVisible(blockReactionOnlineRow, PARTIAL);
        notifyRowIfVisible(markReadAfterSendRow, PARTIAL);

        NotificationCenter.getInstance(UserConfig.selectedAccount).postNotificationName(NotificationCenter.mainUserInfoChanged);
    }

    private int currentPresetIndex() {
        boolean noRead = !NekoConfig.sendReadMessagePackets.Bool();
        boolean noStories = !NekoConfig.sendReadStoriesPackets.Bool();
        boolean noOnline = !NekoConfig.sendOnlinePackets.Bool();
        boolean noTyping = !NekoConfig.sendUploadProgress.Bool();
        boolean autoOffline = NekoConfig.sendOfflinePacketAfterOnline.Bool();
        boolean readAfterSend = NekoConfig.markReadAfterSend.Bool();
        if (noRead && noStories && noOnline && noTyping && autoOffline) {
            return readAfterSend ? 1 : 0;
        }
        if (!noRead && noStories && !noOnline && !noTyping && !autoOffline) {
            return 2;
        }
        return -1;
    }

    private String currentPresetLabel() {
        return switch (currentPresetIndex()) {
            case 0 -> getString(R.string.FlexyGhostPresetFull);
            case 1 -> getString(R.string.FlexyGhostPresetStealth);
            case 2 -> getString(R.string.FlexyGhostPresetStories);
            default -> getString(R.string.FlexyGhostPresetCustom);
        };
    }

    private String formatDelay(int ms) {
        if (ms <= 0) return getString(R.string.FlexyGhostOfflineImmediate);
        if (ms < 1000) return String.format(Locale.US, "%d ms", ms);
        return String.format(Locale.US, "%d s", ms / 1000);
    }

    private void showPresetDialog() {
        if (getParentActivity() == null) return;
        final String[] options = {
                getString(R.string.FlexyGhostPresetFull),
                getString(R.string.FlexyGhostPresetStealth),
                getString(R.string.FlexyGhostPresetStories)
        };
        showDialog(AlertsCreator.createSingleChoiceDialog(getParentActivity(), options,
                getString(R.string.FlexyGhostPresets), Math.max(0, currentPresetIndex()), (dialog, which) -> {
                    NekoConfig.applyGhostPreset(which);
                    AyuState.setAllowReadPacket(false, -1);
                    if (listAdapter != null) listAdapter.notifyDataSetChanged();
                    NotificationCenter.getInstance(UserConfig.selectedAccount).postNotificationName(NotificationCenter.mainUserInfoChanged);
                }));
    }

    private void showOfflineDelayDialog() {
        if (getParentActivity() == null) return;
        final String[] options = new String[OFFLINE_DELAYS.length];
        int selected = 2;
        int current = NekoConfig.ghostOfflineDelayMs.Int();
        for (int i = 0; i < OFFLINE_DELAYS.length; i++) {
            options[i] = formatDelay(OFFLINE_DELAYS[i]);
            if (OFFLINE_DELAYS[i] == current) selected = i;
        }
        showDialog(AlertsCreator.createSingleChoiceDialog(getParentActivity(), options,
                getString(R.string.FlexyGhostOfflineDelay), selected, (dialog, which) -> {
                    if (which >= 0 && which < OFFLINE_DELAYS.length) {
                        NekoConfig.ghostOfflineDelayMs.setConfigInt(OFFLINE_DELAYS[which]);
                        notifyRowIfVisible(offlineDelayRow, PARTIAL);
                    }
                }));
    }

    private void showDeletedMarkDialog() {
        Context context = getParentActivity();
        if (context == null) return;
        ConfigItem config = NaConfig.INSTANCE.getCustomDeletedMark();
        EditTextBoldCursor input = new EditTextBoldCursor(context);
        input.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 18);
        input.setTextColor(Theme.getColor(Theme.key_dialogTextBlack, getResourceProvider()));
        input.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint, getResourceProvider()));
        input.setLineColors(
                Theme.getColor(Theme.key_windowBackgroundWhiteInputField, getResourceProvider()),
                Theme.getColor(Theme.key_windowBackgroundWhiteInputFieldActivated, getResourceProvider()),
                Theme.getColor(Theme.key_text_RedRegular, getResourceProvider()));
        input.setSingleLine(true);
        input.setText(config.String());
        input.setSelection(input.length());

        LinearLayout container = new LinearLayout(context);
        container.setOrientation(LinearLayout.VERTICAL);
        container.addView(input, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 36, 24, 12, 24, 6));

        AlertDialog.Builder builder = new AlertDialog.Builder(context, getResourceProvider());
        builder.setTitle(getString(config.getKey()));
        builder.setView(container);
        builder.setPositiveButton(getString(R.string.Save), (d, w) -> {
            config.setConfigString(input.getText() != null ? input.getText().toString().trim() : "");
            notifyRowIfVisible(customDeletedMarkRow, PARTIAL);
        });
        builder.setNegativeButton(getString(R.string.Cancel), null);
        showDialog(builder.create());
    }

    @Override
    protected void onItemClick(View view, int position, float x, float y) {
        if (position == ghostModeToggleRow) {
            ghostModeMenuExpanded ^= true;
            updateRows();
            listAdapter.notifyItemChanged(ghostModeToggleRow, PARTIAL);
            if (ghostModeMenuExpanded) {
                listAdapter.notifyItemRangeInserted(ghostModeToggleRow + 1, 6);
            } else {
                listAdapter.notifyItemRangeRemoved(ghostModeToggleRow + 1, 6);
            }
        } else if (position == ghostPresetRow) {
            showPresetDialog();
        } else if (position == sendReadMessagePacketsRow) {
            if (!view.isEnabled()) return;
            NekoConfig.sendReadMessagePackets.toggleConfigBool();
            ((CheckBoxCell) view).setChecked(!NekoConfig.sendReadMessagePackets.Bool(), true);
            AyuState.setAllowReadPacket(false, -1);
            updateGhostViews();
        } else if (position == sendReadStoriesPacketsRow) {
            if (!view.isEnabled()) return;
            NekoConfig.sendReadStoriesPackets.toggleConfigBool();
            ((CheckBoxCell) view).setChecked(!NekoConfig.sendReadStoriesPackets.Bool(), true);
            updateGhostViews();
        } else if (position == sendOnlinePacketsRow) {
            if (!view.isEnabled()) return;
            NekoConfig.sendOnlinePackets.toggleConfigBool();
            ((CheckBoxCell) view).setChecked(!NekoConfig.sendOnlinePackets.Bool(), true);
            updateGhostViews();
        } else if (position == sendUploadProgressRow) {
            if (!view.isEnabled()) return;
            NekoConfig.sendUploadProgress.toggleConfigBool();
            ((CheckBoxCell) view).setChecked(!NekoConfig.sendUploadProgress.Bool(), true);
            updateGhostViews();
        } else if (position == sendOfflinePacketAfterOnlineRow) {
            if (!view.isEnabled()) return;
            NekoConfig.sendOfflinePacketAfterOnline.toggleConfigBool();
            ((CheckBoxCell) view).setChecked(NekoConfig.sendOfflinePacketAfterOnline.Bool(), true);
            updateGhostViews();
        } else if (position == blockMentionsReadRow) {
            NekoConfig.ghostBlockMentionsRead.toggleConfigBool();
            ((TextCheckCell) view).setChecked(NekoConfig.ghostBlockMentionsRead.Bool());
        } else if (position == blockReactionOnlineRow) {
            NekoConfig.ghostBlockReactionOnline.toggleConfigBool();
            ((TextCheckCell) view).setChecked(NekoConfig.ghostBlockReactionOnline.Bool());
        } else if (position == offlineDelayRow) {
            showOfflineDelayDialog();
        } else if (position == markReadAfterSendRow) {
            NekoConfig.markReadAfterSend.toggleConfigBool();
            ((TextCheckCell) view).setChecked(NekoConfig.markReadAfterSend.Bool());
            AyuState.setAllowReadPacket(false, -1);
            notifyRowIfVisible(ghostPresetRow, PARTIAL);
        } else if (position == sendWithoutSoundRow) {
            NaConfig.INSTANCE.getSilentMessageByDefault().toggleConfigBool();
            ((TextCheckCell) view).setChecked(NaConfig.INSTANCE.getSilentMessageByDefault().Bool());
        } else if (position == scheduledSendRow) {
            NaConfig.INSTANCE.getGhostScheduledSend().toggleConfigBool();
            ((TextCheckCell) view).setChecked(NaConfig.INSTANCE.getGhostScheduledSend().Bool());
        } else if (position == showGhostInDrawerRow) {
            NekoConfig.showGhostInDrawer.toggleConfigBool();
            ((TextCheckCell) view).setChecked(NekoConfig.showGhostInDrawer.Bool());
            NotificationCenter.getInstance(UserConfig.selectedAccount).postNotificationName(NotificationCenter.mainUserInfoChanged);
        } else if (position == showGhostModeStatusRow) {
            NekoConfig.showGhostModeStatus.toggleConfigBool();
            ((TextCheckCell) view).setChecked(NekoConfig.showGhostModeStatus.Bool());
            NotificationCenter.getInstance(UserConfig.selectedAccount).postNotificationName(NotificationCenter.mainUserInfoChanged);
        } else if (position == keepDeletedRow) {
            NaConfig.INSTANCE.getEnableSaveDeletedMessages().toggleConfigBool();
            updateRows();
            if (listAdapter != null) listAdapter.notifyDataSetChanged();
        } else if (position == translucentDeletedRow) {
            NaConfig.INSTANCE.getTranslucentDeletedMessages().toggleConfigBool();
            ((TextCheckCell) view).setChecked(NaConfig.INSTANCE.getTranslucentDeletedMessages().Bool());
        } else if (position == deletedIconRow) {
            NaConfig.INSTANCE.getUseDeletedIcon().toggleConfigBool();
            updateRows();
            if (listAdapter != null) listAdapter.notifyDataSetChanged();
        } else if (position == customDeletedMarkRow) {
            showDeletedMarkDialog();
        }
    }

    @Override
    protected boolean onItemLongClick(View view, int position, float x, float y) {
        ConfigItem targetItem = null;
        ConfigItem lockedItem = null;

        if (position == sendReadMessagePacketsRow) {
            targetItem = NekoConfig.sendReadMessagePackets;
            lockedItem = NekoConfig.sendReadMessagePacketsLocked;
        } else if (position == sendReadStoriesPacketsRow) {
            targetItem = NekoConfig.sendReadStoriesPackets;
            lockedItem = NekoConfig.sendReadStoriesPacketsLocked;
        } else if (position == sendOnlinePacketsRow) {
            targetItem = NekoConfig.sendOnlinePackets;
            lockedItem = NekoConfig.sendOnlinePacketsLocked;
        } else if (position == sendUploadProgressRow) {
            targetItem = NekoConfig.sendUploadProgress;
            lockedItem = NekoConfig.sendUploadProgressLocked;
        } else if (position == sendOfflinePacketAfterOnlineRow) {
            targetItem = NekoConfig.sendOfflinePacketAfterOnline;
            lockedItem = NekoConfig.sendOfflinePacketAfterOnlineLocked;
        }

        if (lockedItem != null && targetItem != null) {
            boolean currentLocked = lockedItem.Bool();
            if (!currentLocked && getGhostModeLockedCount() >= 4) {
                AndroidUtilities.shakeViewSpring(view, -4);
                return true;
            }
            lockedItem.setConfigBool(!currentLocked);
            view.setEnabled(currentLocked);
            notifyRowIfVisible(ghostModeToggleRow, PARTIAL);
            return true;
        }
        return super.onItemLongClick(view, position, x, y);
    }

    @Override
    protected String getActionBarTitle() {
        return getString(R.string.GhostMode);
    }

    @Override
    protected BaseListAdapter createAdapter(Context context) {
        return new ListAdapter(context);
    }

    private int getGhostModeSelectedCount() {
        int count = 0;
        if (!NekoConfig.sendReadMessagePackets.Bool()) count++;
        if (!NekoConfig.sendReadStoriesPackets.Bool()) count++;
        if (!NekoConfig.sendOnlinePackets.Bool()) count++;
        if (!NekoConfig.sendUploadProgress.Bool()) count++;
        if (NekoConfig.sendOfflinePacketAfterOnline.Bool()) count++;
        return count;
    }

    private int getGhostModeLockedCount() {
        int count = 0;
        if (NekoConfig.sendReadMessagePacketsLocked.Bool()) count++;
        if (NekoConfig.sendReadStoriesPacketsLocked.Bool()) count++;
        if (NekoConfig.sendOnlinePacketsLocked.Bool()) count++;
        if (NekoConfig.sendUploadProgressLocked.Bool()) count++;
        if (NekoConfig.sendOfflinePacketAfterOnlineLocked.Bool()) count++;
        return count;
    }

    private class ListAdapter extends BaseListAdapter {

        public ListAdapter(Context context) {
            super(context);
        }

        @Override
        public boolean isEnabled(RecyclerView.ViewHolder holder) {
            int type = holder.getItemViewType();
            if (type == TYPE_CHECKBOX2) {
                return holder.itemView.isEnabled();
            }
            return type == TYPE_CHECK || type == TYPE_CHECK2 || type == TYPE_SETTINGS;
        }

        @Override
        public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position, boolean payload) {
            switch (holder.getItemViewType()) {
                case TYPE_SHADOW:
                    holder.itemView.setBackground(Theme.getThemedDrawable(mContext, R.drawable.greydivider, Theme.key_windowBackgroundGrayShadow));
                    break;
                case TYPE_SETTINGS:
                    TextSettingsCell settingsCell = (TextSettingsCell) holder.itemView;
                    if (position == ghostPresetRow) {
                        settingsCell.setTextAndValue(getString(R.string.FlexyGhostPresets), currentPresetLabel(), false);
                    } else if (position == offlineDelayRow) {
                        settingsCell.setTextAndValue(getString(R.string.FlexyGhostOfflineDelay),
                                formatDelay(NekoConfig.ghostOfflineDelayMs.Int()), true);
                    } else if (position == customDeletedMarkRow) {
                        ConfigItem mark = NaConfig.INSTANCE.getCustomDeletedMark();
                        settingsCell.setTextAndValue(getString(mark.getKey()), mark.String(), false);
                    }
                    break;
                case TYPE_CHECK:
                    TextCheckCell textCheckCell = (TextCheckCell) holder.itemView;
                    textCheckCell.setEnabled(true, null);
                    if (position == blockMentionsReadRow) {
                        textCheckCell.setTextAndCheck(getString(R.string.FlexyGhostBlockMentionsRead), NekoConfig.ghostBlockMentionsRead.Bool(), true);
                    } else if (position == blockReactionOnlineRow) {
                        textCheckCell.setTextAndCheck(getString(R.string.FlexyGhostBlockReactionOnline), NekoConfig.ghostBlockReactionOnline.Bool(), true);
                    } else if (position == markReadAfterSendRow) {
                        textCheckCell.setTextAndCheck(getString(R.string.MarkReadAfterSend), NekoConfig.markReadAfterSend.Bool(), true);
                    } else if (position == sendWithoutSoundRow) {
                        textCheckCell.setTextAndCheck(getString(R.string.SilentMessageByDefault), NaConfig.INSTANCE.getSilentMessageByDefault().Bool(), true);
                    } else if (position == scheduledSendRow) {
                        textCheckCell.setTextAndCheck(getString(R.string.GhostScheduledSend), NaConfig.INSTANCE.getGhostScheduledSend().Bool(), true);
                    } else if (position == showGhostInDrawerRow) {
                        textCheckCell.setTextAndCheck(getString(R.string.GhostModeInDrawer), NekoConfig.showGhostInDrawer.Bool(), true);
                    } else if (position == showGhostModeStatusRow) {
                        textCheckCell.setTextAndCheck(getString(R.string.GhostModeStatusIndicator), NekoConfig.showGhostModeStatus.Bool(), false);
                    } else if (position == keepDeletedRow) {
                        textCheckCell.setTextAndCheck(getString(R.string.FlexyGhostKeepDeleted),
                                NaConfig.INSTANCE.getEnableSaveDeletedMessages().Bool(), translucentDeletedRow >= 0);
                    } else if (position == translucentDeletedRow) {
                        ConfigItem item = NaConfig.INSTANCE.getTranslucentDeletedMessages();
                        textCheckCell.setTextAndCheck(getString(item.getKey()), item.Bool(), true);
                    } else if (position == deletedIconRow) {
                        ConfigItem item = NaConfig.INSTANCE.getUseDeletedIcon();
                        textCheckCell.setTextAndCheck(getString(item.getKey()), item.Bool(), customDeletedMarkRow >= 0);
                    }
                    break;
                case TYPE_HEADER:
                    HeaderCell headerCell = (HeaderCell) holder.itemView;
                    if (position == ghostEssentialsHeaderRow) {
                        headerCell.setText(getString(R.string.GhostEssentialsHeader));
                    } else if (position == ghostAdvancedHeaderRow) {
                        headerCell.setText(getString(R.string.FlexyGhostAdvancedHeader));
                    } else if (position == deletedHeaderRow) {
                        headerCell.setText(getString(R.string.FlexyGhostDeletedHeader));
                    }
                    break;
                case TYPE_INFO_PRIVACY:
                    TextInfoPrivacyCell cell = (TextInfoPrivacyCell) holder.itemView;
                    cell.setBackground(Theme.getThemedDrawable(mContext, R.drawable.greydivider, Theme.key_windowBackgroundGrayShadow));
                    if (position == ghostModeNoticeRow) {
                        cell.setText(getString(R.string.GhostModeNotice));
                    } else if (position == markReadAfterSendNoticeRow) {
                        cell.setText(getString(R.string.MarkReadAfterSendNotice));
                    } else if (position == sendWithoutSoundNoticeRow) {
                        cell.setText(getString(R.string.SendWithoutSoundRowNotice));
                    } else if (position == scheduledSendNoticeRow) {
                        cell.setText(getString(R.string.GhostScheduledSendNotice));
                    } else if (position == deletedNoticeRow) {
                        cell.setText(getString(R.string.FlexyGhostKeepDeletedNotice));
                    }
                    break;
                case TYPE_CHECK2:
                    TextCheckCell2 checkCell = (TextCheckCell2) holder.itemView;
                    if (position == ghostModeToggleRow) {
                        int selectedCount = getGhostModeSelectedCount();
                        boolean isActive = NekoConfig.isGhostModeActive();
                        checkCell.setTextAndCheck(getString(R.string.GhostMode), isActive, true, true);
                        checkCell.setCollapseArrow(String.format(Locale.US, "%d/5", selectedCount), !ghostModeMenuExpanded, () -> {
                            NekoConfig.toggleGhostMode();
                            boolean nowActive = NekoConfig.isGhostModeActive();
                            String msg = nowActive
                                    ? getString(R.string.GhostModeEnabled)
                                    : getString(R.string.GhostModeDisabled);
                            BulletinFactory.of(getLastFragment()).createSuccessBulletin(msg).show();
                            updateGhostViews();
                        });
                    }
                    checkCell.getCheckBox().setColors(Theme.key_switchTrack, Theme.key_switchTrackChecked, Theme.key_windowBackgroundWhite, Theme.key_windowBackgroundWhite);
                    checkCell.getCheckBox().setDrawIconType(0);
                    break;
                case TYPE_CHECKBOX2:
                    CheckBoxCell checkBoxCell = (CheckBoxCell) holder.itemView;
                    ConfigItem item = null;
                    ConfigItem lockedItem = null;
                    boolean checkValue = false;
                    String title = "";

                    if (position == sendReadMessagePacketsRow) {
                        item = NekoConfig.sendReadMessagePackets;
                        lockedItem = NekoConfig.sendReadMessagePacketsLocked;
                        checkValue = !item.Bool();
                        title = getString(R.string.DontSendReadMessagePackets);
                    } else if (position == sendReadStoriesPacketsRow) {
                        item = NekoConfig.sendReadStoriesPackets;
                        lockedItem = NekoConfig.sendReadStoriesPacketsLocked;
                        checkValue = !item.Bool();
                        title = getString(R.string.DontReadStoriesPackets);
                    } else if (position == sendOnlinePacketsRow) {
                        item = NekoConfig.sendOnlinePackets;
                        lockedItem = NekoConfig.sendOnlinePacketsLocked;
                        checkValue = !item.Bool();
                        title = getString(R.string.DontSendOnlinePackets);
                    } else if (position == sendUploadProgressRow) {
                        item = NekoConfig.sendUploadProgress;
                        lockedItem = NekoConfig.sendUploadProgressLocked;
                        checkValue = !item.Bool();
                        title = getString(R.string.DontSendUploadProgress);
                    } else if (position == sendOfflinePacketAfterOnlineRow) {
                        item = NekoConfig.sendOfflinePacketAfterOnline;
                        lockedItem = NekoConfig.sendOfflinePacketAfterOnlineLocked;
                        checkValue = item.Bool();
                        title = getString(R.string.SendOfflinePacketAfterOnline);
                    }

                    if (item != null && lockedItem != null) {
                        boolean isLocked = lockedItem.Bool();
                        checkBoxCell.setText(title, "", checkValue, true, true);
                        checkBoxCell.setEnabled(!isLocked);
                    }
                    checkBoxCell.setPad(1);
                    break;
            }
        }

        @Override
        public int getItemViewType(int position) {
            if (position == ghostEssentialsHeaderRow || position == ghostAdvancedHeaderRow || position == deletedHeaderRow) {
                return TYPE_HEADER;
            } else if (position == ghostEndDividerRow) {
                return TYPE_SHADOW;
            } else if (position == ghostModeNoticeRow || position == markReadAfterSendNoticeRow
                    || position == sendWithoutSoundNoticeRow || position == scheduledSendNoticeRow
                    || position == deletedNoticeRow) {
                return TYPE_INFO_PRIVACY;
            } else if (position == ghostPresetRow || position == offlineDelayRow || position == customDeletedMarkRow) {
                return TYPE_SETTINGS;
            } else if (position == ghostModeToggleRow) {
                return TYPE_CHECK2;
            } else if (position >= sendReadMessagePacketsRow && position <= sendOfflinePacketAfterOnlineRow) {
                return TYPE_CHECKBOX2;
            }
            return TYPE_CHECK;
        }
    }
}
