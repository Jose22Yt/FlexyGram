package app.exteraless.settings;

import static org.telegram.messenger.LocaleController.getString;
import static org.telegram.messenger.LocaleController.formatString;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.text.InputType;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.R;
import org.telegram.messenger.LiteMode;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextDetailSettingsCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Cells.TextSettingsCell;
import org.telegram.ui.Components.BulletinFactory;
import org.telegram.ui.LiteModeSettingsActivity;
import org.telegram.ui.Components.EditTextBoldCursor;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.RecyclerListView;
import org.telegram.ui.LaunchActivity;
import org.telegram.ui.MainTabsLayout;

import app.exteraless.appearance.AppearanceConfig;
import app.exteraless.appearance.AvatarCornersPreviewCell;
import app.exteraless.appearance.AvatarCornersSeekBar;
import app.exteraless.appearance.ChatListPreviewCell;
import app.exteraless.appearance.FabShapeCell;
import app.exteraless.appearance.FoldersPreviewCell;
import app.exteraless.icons.IconPacksActivity;
import app.exteraless.pillstack.PillStackSettingsActivity;
import tw.nekomimi.nekogram.NekoConfig;
import tw.nekomimi.nekogram.config.ConfigItem;
import tw.nekomimi.nekogram.helpers.AppRestartHelper;
import tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity;
import tw.nekomimi.nekogram.settings.NekoEmojiSettingsActivity;
import tw.nekomimi.nekogram.ui.cells.HeaderCell;
import xyz.nextalone.nagram.NaConfig;


/**
 * Экран «Оформление» раздела openExtera — визуальный порт AppearancePreferencesActivity
 * из exteraGram. Живые превью (аватарки, список чатов, папки) портированы 1:1 из
 * exteraGram 10.10.1 в пакет {@link app.exteraless.appearance}.
 *
 * Настройки, у которых в NagramX уже есть аналог, привязаны к существующим ConfigItem
 * (NaConfig / NekoConfig). Чисто визуальные настройки, которых в NagramX нет,
 * хранятся в {@link AppearanceConfig} и помечены в отчёте как «только UI».
 */
public class OpenExteraAppearanceActivity extends app.flexygram.settings.SignatureMatteSettingsActivity {

    private static final int TYPE_AVATAR_CORNERS = 100;
    private static final int TYPE_CHAT_LIST = 101;
    private static final int TYPE_FOLDERS = 102;
    private static final int TYPE_SECTION_SLIDER = 103;
    /** Две карточки-превью формы плавающей кнопки. */
    private static final int TYPE_FAB_SHAPE = 106;

    private int avatarsHeaderRow, iconsHeaderRow, iconsDividerRow;

    // Appearance
    private int appearanceHeaderRow;
    private int fabShapeRow;
    private int useSystemFontsRow;
    private int gooeyAvatarRow;
    private int customThemesRow;
    private int appearanceDividerRow;

    // Sections (UI only)
    private int sectionsHeaderRow;
    private int sectionRadiusRow;
    private int separateHeadersRow;
    private int dividerStyleRow;
    private int sectionsDividerRow;

    // Blur
    private int blurHeaderRow;
    private int glassOutlineRow;
    private int glassMessageMenuRow;
    private int forceBlurRow;
    private int disableAvatarBlurRow;
    private int blurDividerRow;

    // Avatar corners
    private int avatarCornersPreviewRow;
    private int singleCornerRadiusRow;
    private int avatarsDividerRow;

    // Chat list
    private int chatListHeaderRow;
    private int chatListPreviewRow;
    private int forceSnowRow;
    private int centerTitleRow;
    private int senderMiniAvatarsRow;
    private int titleTextRow;
    private int chatListDividerRow;

    // Folders
    private int foldersHeaderRow;
    private int foldersPreviewRow;
    private int folderThemeAccentRow;
    private int tabTitleStyleRow;
    private int tabCounterRow;
    private int foldersDividerRow;

    // Links
    private int linksHeaderRow;
    private int appNavigationRow;
    private int flexyLiquidNavigationRow,flexyShareRow;
    private int iconPacksRow;
    private int emojiSetsRow;
    private int pillStackRow;
    private int hidingRow;
    private int linksDividerRow;

    private AvatarCornersPreviewCell avatarCornersPreviewCell;
    private ChatListPreviewCell chatListPreviewCell;
    private FoldersPreviewCell foldersPreviewCell;
    private FabShapeCell fabShapeCell;

    /**
     * Отложенный rebuild после слайдера радиуса секций. exteraGram
     * (handleSectionRadiusChange :335-343) зовёт rebuildFragments на каждое изменение,
     * но у него слайдер — Material-виджет с редкими колбэками; наш SeekBarView отдаёт
     * значение на каждый dp, и пересборка всех фрагментов на каждом шаге даёт рывки.
     */
    private final Runnable sectionRadiusRebuild = this::rebuildAll;

    public OpenExteraAppearanceActivity() {
        super();
        AppearanceConfig.init();
    }

    @Override
    protected void updateRows() {
        super.updateRows();

        avatarsHeaderRow = addRow("matteAvatarsHeader");
        avatarCornersPreviewRow = addRow("avatarCorners");
        singleCornerRadiusRow = addRow("singleCornerRadius");
        avatarsDividerRow = addRow();

        chatListHeaderRow = addRow("chatListHeader");
        chatListPreviewRow = addRow("chatListPreview");
        forceSnowRow = addRow("forceSnow");
        centerTitleRow = addRow("centerTitle");
        senderMiniAvatarsRow = addRow("senderMiniAvatars");
        titleTextRow = addRow("titleText");
        chatListDividerRow = addRow();

        foldersHeaderRow = addRow("foldersHeader");
        foldersPreviewRow = addRow("foldersPreview");
        folderThemeAccentRow = addRow("folderThemeAccent");
        tabTitleStyleRow = addRow("tabTitleStyle");
        tabCounterRow = addRow("tabCounter");
        foldersDividerRow = addRow();

        iconsHeaderRow = addRow("matteIconsHeader");
        iconPacksRow = addRow("iconPacks");
        emojiSetsRow = addRow("emojiSets", "EmojiSets");
        iconsDividerRow = addRow();

        linksHeaderRow = addRow("linksHeader");
        appNavigationRow = addRow("appNavigation");
        flexyLiquidNavigationRow = addRow("flexyLiquidNavigation");
        flexyShareRow=addRow("flexyShareSheet");
        pillStackRow = addRow("pillStack");
        hidingRow = addRow("hiding");
        linksDividerRow = addRow();

        appearanceHeaderRow = addRow("appearanceHeader");
        fabShapeRow = addRow("fabShape");
        useSystemFontsRow = addRow("useSystemFonts");
        customThemesRow = addRow("customThemes");
        appearanceDividerRow = addRow();

        sectionsHeaderRow = addRow("sectionsHeader");
        sectionRadiusRow = addRow("sectionRadius");
        separateHeadersRow = addRow("separateHeaders");
        dividerStyleRow = addRow("dividerStyle");
        sectionsDividerRow = addRow();

        blurHeaderRow = addRow("blurHeader");
        gooeyAvatarRow = addRow("gooeyAvatar");
        glassOutlineRow = addRow("glassOutline");
        glassMessageMenuRow = addRow("glassMessageMenu");
        forceBlurRow = addRow("forceBlur");
        disableAvatarBlurRow = addRow("disableAvatarBlur");
        blurDividerRow = addRow();

    }

    @Override
    protected String getActionBarTitle() {
        return getString(R.string.OEAppearanceTitle);
    }

    @Override
    public int getSearchGuid() {
        return 21000;
    }

    @Override
    public int getSearchIcon() {
        return R.drawable.msg_theme;
    }

    @Override
    public String getSearchPrefix() {
        return "OEAppearance";
    }

    @Override
    protected String getKey() {
        return "exteraless_appearance";
    }

    @Override
    protected BaseListAdapter createAdapter(Context context) {
        return new ListAdapter(context);
    }

    /**
     * Пересобрать список строк. Нужен там, где меняется их состав: базовый класс
     * зовёт updateRows() только в onFragmentCreate, поэтому одного
     * notifyDataSetChanged недостаточно.
     */
    private void rebuildRowsAndNotify() {
        updateRows();
        if (listAdapter != null) {
            listAdapter.notifyDataSetChanged();
        }
    }

    private void rebuildAll() {
        if (parentLayout != null) {
            parentLayout.rebuildAllFragmentViews(false, false);
        }
    }

    private void showPowerSaverNotice() {
        if (!LiteMode.isPowerSaverApplied() || getParentActivity() == null) {
            return;
        }
        BulletinFactory.of(this)
                .createSimpleBulletin(R.raw.info,
                        formatString(R.string.OEAppearancePowerSaverActive, LiteMode.getPowerSaverLevel()),
                        getString(R.string.OEAppearancePowerSaverSettings),
                        () -> presentFragment(new LiteModeSettingsActivity()))
                .show();
    }

    /**
     * Пересобрать чужие экраны и обновить этот.
     *
     * rebuildAllFragmentViews(false, ...) намеренно пропускает последний фрагмент
     * стека — то есть ровно тот, который открыт. Свои строки поэтому обновляем
     * сами: галочки внутри группы и счётчик «N/8» ставятся при привязке, а стиль
     * переключателей и слайдеров читается при отрисовке.
     */
    private void notifyRow(int row) {
        if (listAdapter != null && row >= 0) {
            listAdapter.notifyItemChanged(row);
        }
    }

    private void showRestartHint() {
        if (getParentActivity() == null) {
            return;
        }
        BulletinFactory.of(this)
                .createSimpleBulletin(R.raw.info, getString(R.string.OEAppearanceNeedRestart),
                        getString(R.string.OEAppearanceRestartNow),
                        () -> {
                            Activity activity = getParentActivity();
                            if (activity != null) {
                                AppRestartHelper.triggerRebirth(activity,
                                        new Intent(activity, LaunchActivity.class));
                            }
                        })
                .show();
    }

    private void showSelector(int position, String title, CharSequence[] items, ConfigItem item, Runnable after) {
        if (getParentActivity() == null) {
            return;
        }
        AlertDialog.Builder builder = new AlertDialog.Builder(getParentActivity());
        builder.setTitle(title);
        builder.setItems(items, (dialog, which) -> {
            item.setConfigInt(which);
            if (listAdapter != null) {
                listAdapter.notifyItemChanged(position);
            }
            if (after != null) {
                after.run();
            }
        });
        builder.setNegativeButton(getString(R.string.Cancel), null);
        showDialog(builder.create());
    }

    private CharSequence[] titleTextOptions() {
        return new CharSequence[]{
                getString(R.string.OEAppearanceTitleTextApp),
                getString(R.string.OEAppearanceTitleTextUsername),
                getString(R.string.OEAppearanceTitleTextName),
                getString(R.string.FilterChats),
                getString(R.string.OEAppearanceTitleTextCustom)
        };
    }

    private void showTitleTextSelector(Runnable onChanged) {
        if (getParentActivity() == null) {
            return;
        }
        AlertDialog.Builder builder = new AlertDialog.Builder(getParentActivity());
        builder.setTitle(getString(R.string.OEAppearanceTitleText));
        builder.setItems(titleTextOptions(), (dialog, which) -> {
            if (which == AppearanceConfig.TITLE_TEXT_CUSTOM) {
                showCustomTitleDialog(onChanged);
            } else {
                setTitleText(which, onChanged);
            }
        });
        builder.setNegativeButton(getString(R.string.Cancel), null);
        showDialog(builder.create());
    }

    private void setTitleText(int value, Runnable onChanged) {
        AppearanceConfig.titleText.setConfigInt(value);
        if (listAdapter != null) {
            listAdapter.notifyItemChanged(titleTextRow);
        }
        onChanged.run();
    }

    private void showCustomTitleDialog(Runnable onChanged) {
        Context context = getParentActivity();
        if (context == null) {
            return;
        }
        ConfigItem customTitle = NaConfig.INSTANCE.getCustomTitle();

        EditTextBoldCursor editText = new EditTextBoldCursor(context);
        editText.lineYFix = true;
        editText.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 18);
        if (!customTitle.defaultValue.equals(customTitle.String())) {
            editText.setText(customTitle.String());
        }
        editText.setTextColor(getThemedColor(Theme.key_dialogTextBlack));
        editText.setHintColor(getThemedColor(Theme.key_groupcreate_hintText));
        editText.setHintText(getString(R.string.OEAppearanceTitleTextApp));
        editText.setFocusable(true);
        editText.setSingleLine(true);
        editText.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        editText.setBackground(null);
        editText.setLineColors(getThemedColor(Theme.key_windowBackgroundWhiteInputField),
                getThemedColor(Theme.key_windowBackgroundWhiteInputFieldActivated),
                getThemedColor(Theme.key_text_RedRegular));
        editText.setCursorColor(getThemedColor(Theme.key_windowBackgroundWhiteInputFieldActivated));
        editText.setPadding(0, AndroidUtilities.dp(6), 0, AndroidUtilities.dp(6));

        LinearLayout container = new LinearLayout(context);
        container.setOrientation(LinearLayout.VERTICAL);
        container.addView(editText, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT,
                LayoutHelper.WRAP_CONTENT, 24f, 0f, 24f, 10f));

        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle(getString(R.string.OEAppearanceTitleText));
        builder.makeCustomMaxHeight();
        builder.setView(container);
        builder.setWidth(AndroidUtilities.dp(292));
        builder.setPositiveButton(getString(R.string.Done), (dialog, which) -> {
            String value = editText.getText() == null ? "" : editText.getText().toString().trim();
            if (TextUtils.isEmpty(value)) {
                customTitle.setConfigString((String) customTitle.defaultValue);
                setTitleText(0, onChanged);
            } else {
                customTitle.setConfigString(value);
                setTitleText(AppearanceConfig.TITLE_TEXT_CUSTOM, onChanged);
            }
        });
        builder.setNegativeButton(getString(R.string.Cancel), null);

        AlertDialog dialog = builder.create();
        dialog.setOnShowListener(d -> {
            editText.requestFocus();
            editText.setSelection(editText.length());
            AndroidUtilities.showKeyboard(editText);
        });
        showDialog(dialog, d -> AndroidUtilities.hideKeyboard(editText));
    }

    /**
     * Порядок пунктов «Folder Title» — «Names with Icons», «Names only», «Icons only»;
     * у NekoConfig.tabsTitleType значения 0 TEXT, 1 ICON, 2 MIX.
     * Массив переводит индекс диалога в значение конфига.
     */
    private static final int[] TAB_TITLE_ORDER = {2, 0, 1};

    private CharSequence[] tabTitleOptions() {
        return new CharSequence[]{
                getString(R.string.OEAppearanceTabTitleStyleTextWithIcons),
                getString(R.string.OEAppearanceTabTitleStyleTextOnly),
                getString(R.string.OEAppearanceTabTitleStyleIconsOnly)
        };
    }

    /** Значение конфига -> индекс в {@link #tabTitleOptions()}. */
    private static int tabTitleIndex(int configValue) {
        for (int i = 0; i < TAB_TITLE_ORDER.length; i++) {
            if (TAB_TITLE_ORDER[i] == configValue) {
                return i;
            }
        }
        return 0;
    }

    private void onDividerStyleChanged() {
        // 0 — скрыт, 1 — линия, 2 — сегменты. Скрытый привязываем к реальному NaConfig.hideDividers,
        // чтобы не разъезжался экран NekoGeneralSettingsActivity.
        NaConfig.INSTANCE.getHideDividers().setConfigBool(AppearanceConfig.dividerStyle.Int() == 0);
        // Theme.getColor читает закешированное значение — сбросить кэш обязательно.
        AppearanceConfig.invalidateDividerStyle();
        // «Сегменты» рисуются раздельными карточками, и заголовок обязан быть своей карточкой,
        // иначе секция склеивается — настройка дожимается принудительно.
        if (AppearanceConfig.dividerStyle.Int() == AppearanceConfig.DIVIDER_SEGMENTS
                && !AppearanceConfig.separateHeaders.Bool()) {
            AppearanceConfig.separateHeaders.setConfigBool(true);
        }
        if (listAdapter != null) {
            listAdapter.notifyItemChanged(separateHeadersRow);
        }
        // Цвет разделителя лежит в общей теме,
        // без applyCommonTheme новые значения не подхватят уже созданные ячейки.
        Theme.applyCommonTheme();
        if (listView != null) {
            listView.invalidate();
            listView.invalidateItemDecorations();
        }
        invalidatePreviews();
        rebuildAll();
    }

    /**
     * Новый радиус надо занести в декоратор
     * списка и перерисовать его, иначе на текущем экране ничего не меняется.
     */
    private void onSectionRadiusChanged(int value) {
        AppearanceConfig.sectionRadius.setConfigInt(value);
        if (listView != null) {
            listView.setSections(AndroidUtilities.dp(12), AndroidUtilities.dp(value), true);
            listView.invalidate();
            listView.invalidateItemDecorations();
        }
        AndroidUtilities.cancelRunOnUIThread(sectionRadiusRebuild);
        AndroidUtilities.runOnUIThread(sectionRadiusRebuild, 350);
    }

    /** Все живые превью экрана — их надо дёргать на смене темы и стиля разделителя. */
    private void invalidatePreviews() {
        if (avatarCornersPreviewCell != null) avatarCornersPreviewCell.invalidate();
        if (chatListPreviewCell != null) chatListPreviewCell.invalidate();
        if (foldersPreviewCell != null) foldersPreviewCell.invalidate();
        if (fabShapeCell != null) fabShapeCell.invalidate();
    }

    @Override
    protected void onItemClick(View view, int position, float x, float y) {
        if (position == iconPacksRow) {
            presentFragment(new IconPacksActivity());
            return;
        } else if (position == pillStackRow) {
            presentFragment(new PillStackSettingsActivity());
            return;
        } else if (position == appNavigationRow) {
            presentFragment(new OpenExteraAppNavigationActivity());
            return;
        } else if(position==flexyShareRow){
            presentFragment(new app.flexygram.share.FlexyShareSettingsActivity());
        } else if (position == flexyLiquidNavigationRow) {
            presentFragment(new app.flexygram.navigation.LiquidNavigationSettingsActivity());
            return;
        } else if (position == emojiSetsRow) {
            presentFragment(new NekoEmojiSettingsActivity());
            return;
        } else if (position == hidingRow) {
            presentFragment(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_HIDING));
            return;
        } else if (position == dividerStyleRow) {
            showSelector(position, getString(R.string.OEAppearanceDividerStyle), new CharSequence[]{
                    getString(R.string.OEAppearanceDividerHidden),
                    getString(R.string.OEAppearanceDividerLine),
                    getString(R.string.OEAppearanceDividerSegments)
            }, AppearanceConfig.dividerStyle, this::onDividerStyleChanged);
            return;
        } else if (position == glassOutlineRow) {
            showSelector(position, getString(R.string.OEAppearanceGlassOutline), new CharSequence[]{
                    getString(R.string.OEAppearanceGlassOutlineGlare),
                    getString(R.string.OEAppearanceGlassOutlineSolid),
                    getString(R.string.OEAppearanceGlassOutlineHidden)
            }, AppearanceConfig.glassOutlineStyle, null);
            return;
        } else if (position == folderThemeAccentRow) {
            AppearanceConfig.folderThemeAccent.toggleConfigBool();
            if(view instanceof TextCheckCell)((TextCheckCell)view).setChecked(AppearanceConfig.folderThemeAccent.Bool());
            if(foldersPreviewCell!=null)foldersPreviewCell.invalidate();
            return;
        } else if (position == tabTitleStyleRow) {
            if (getParentActivity() == null) {
                return;
            }
            // Порядок пунктов диалога свой, значения NekoConfig.tabsTitleType тоже
            // (0 TEXT, 1 ICON, 2 MIX),
            // поэтому индекс диалога отображается через TAB_TITLE_ORDER.
            AlertDialog.Builder builder = new AlertDialog.Builder(getParentActivity());
            builder.setTitle(getString(R.string.OEAppearanceTabTitleStyle));
            builder.setItems(tabTitleOptions(), (dialog, which) -> {
                NekoConfig.tabsTitleType.setConfigInt(TAB_TITLE_ORDER[clamp(which, TAB_TITLE_ORDER.length)]);
                if (listAdapter != null) {
                    listAdapter.notifyItemChanged(position);
                }
                if (foldersPreviewCell != null) {
                    foldersPreviewCell.updateTabTitle(true);
                    foldersPreviewCell.updateTabIcons(true);
                }
                getNotificationCenter().postNotificationName(NotificationCenter.dialogFiltersUpdated);
            });
            builder.setNegativeButton(getString(R.string.Cancel), null);
            showDialog(builder.create());
            return;
        } else if (position == tabCounterRow) {
            showSelector(position, getString(R.string.OEAppearanceTabCounter), new CharSequence[]{
                    getString(R.string.OEAppearanceTabCounterAll),
                    getString(R.string.OEAppearanceTabCounterUnmuted),
                    getString(R.string.OEAppearanceTabCounterOff)
            }, NaConfig.INSTANCE.getIgnoreUnreadCount(), () -> {
                if (foldersPreviewCell != null) {
                    foldersPreviewCell.updateTabCounter(true);
                }
                showRestartHint();
            });
            return;
        } else if (position == centerTitleRow) {
            // Обычный переключатель, а не селектор из четырёх пунктов:
            // центровка либо есть, либо нет.
            AppearanceConfig.setCenterTitle(!AppearanceConfig.centerTitle());
            if (view instanceof org.telegram.ui.Cells.TextCheckCell) {
                ((org.telegram.ui.Cells.TextCheckCell) view)
                        .setChecked(AppearanceConfig.INSTANCE.centerTitle());
            }
            if (chatListPreviewCell != null) {
                chatListPreviewCell.updateCentered(true);
            }
            rebuildAll();
            return;
        } else if (position == titleTextRow) {
            Runnable onTitleTextChanged = () -> {
                if (chatListPreviewCell != null) {
                    chatListPreviewCell.updateTitle(true);
                    // Эмодзи-статус стоит вплотную к заголовку, и его позиция зависит от длины
                    // текста.
                    chatListPreviewCell.updateStatus(true);
                }
                getNotificationCenter().postNotificationName(
                        NotificationCenter.currentUserPremiumStatusChanged);
                // Сам заголовок списка чатов ставится один раз в DialogsActivity.createView
                // (:3645), по уведомлению он не переустанавливается — нужна пересборка вьюх.
                rebuildAll();
            };
            showTitleTextSelector(onTitleTextChanged);
            return;
        } else if (position == forceSnowRow) {
            boolean enabled = NekoConfig.actionBarDecoration.Int() != 1;
            NekoConfig.actionBarDecoration.setConfigInt(enabled ? 1 : 0);
            NaConfig.INSTANCE.getChatDecoration().setConfigInt(enabled ? 1 : 0);
            if (view instanceof TextCheckCell) {
                ((TextCheckCell) view).setChecked(enabled);
            }
            rebuildAll();
            if (enabled) {
                showPowerSaverNotice();
            }
            return;
        } else if (position == forceBlurRow) {
            boolean enabled = !LiteMode.isEnabledSetting(LiteMode.FLAG_CHAT_BLUR);
            LiteMode.toggleFlag(LiteMode.FLAG_CHAT_BLUR, enabled);
            if (view instanceof TextCheckCell) {
                ((TextCheckCell) view).setChecked(enabled);
            }
            rebuildAll();
            if (enabled) {
                showPowerSaverNotice();
            }
            return;
        } else if (position == glassMessageMenuRow) {
            boolean enabled = AppearanceConfig.glassMessageMenu.toggleConfigBool();
            if (view instanceof TextCheckCell) {
                ((TextCheckCell) view).setChecked(enabled);
            }
            // Стеклянное меню рисуется поверх
            // блюра, и без него настройка не даёт ничего видимого, поэтому предлагаем включить.
            if (enabled && !LiteMode.isEnabledSetting(LiteMode.FLAG_CHAT_BLUR) && getParentActivity() != null) {
                BulletinFactory.of(this)
                        .createSimpleBulletin(R.raw.info,
                                getString(R.string.OEAppearanceGlassMessageMenuBlurOff),
                                getString(R.string.Enable),
                                () -> {
                                    LiteMode.toggleFlag(LiteMode.FLAG_CHAT_BLUR, true);
                                    notifyRow(forceBlurRow);
                                    rebuildAll();
                                    showPowerSaverNotice();
                                })
                        .show();
            } else if (enabled) {
                showPowerSaverNotice();
            }
            return;
        } else if (position == separateHeadersRow
                && AppearanceConfig.sectionsSeparatedHeadersForced()) {
            // При «Сегментах» строка нарисована выключенной,
            // клик по ней ничего не меняет.
            return;
        }

        ConfigItem item = null;
        boolean rebuild = false;
        boolean restart = false;
        boolean clearTypefaces = false;

        if (position == useSystemFontsRow) {
            item = NekoConfig.typeface;
            restart = true;
            clearTypefaces = true;
        } else if (position == gooeyAvatarRow) {
            item = AppearanceConfig.gooeyAvatarAnimation;
        } else if (position == customThemesRow) {
            item = AppearanceConfig.customThemes;
        } else if (position == separateHeadersRow) {
            item = AppearanceConfig.separateHeaders;
        } else if (position == disableAvatarBlurRow) {
            item = NaConfig.INSTANCE.getDisableAvatarBlur();
            rebuild = true;
        } else if (position == singleCornerRadiusRow) {
            item = AppearanceConfig.singleCornerRadius;
            rebuild = true;
        } else if (position == senderMiniAvatarsRow) {
            item = AppearanceConfig.senderMiniAvatars;
        }

        if (item == null) {
            return;
        }

        boolean value = item.toggleConfigBool();
        if (clearTypefaces) {
            AndroidUtilities.clearTypefaceCache();
        }
        if (view instanceof TextCheckCell) {
            ((TextCheckCell) view).setChecked(value);
        }
        if (rebuild) {
            rebuildAll();
        }
        if (restart) {
            showRestartHint();
        }
    }

    private class ListAdapter extends MatteListAdapter {

        public ListAdapter(Context context) {
            super(context);
        }

        @NonNull
        @Override
        public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            View view;
            switch (viewType) {
                case TYPE_AVATAR_CORNERS:
                    avatarCornersPreviewCell = new AvatarCornersPreviewCell(mContext,
                            OpenExteraAppearanceActivity.this::rebuildAll);
                    avatarCornersPreviewCell.setNeedDivider(true);
                    view = avatarCornersPreviewCell;
                    break;
                case TYPE_CHAT_LIST:
                    chatListPreviewCell = new ChatListPreviewCell(mContext);
                    view = chatListPreviewCell;
                    break;
                case TYPE_FOLDERS:
                    foldersPreviewCell = new FoldersPreviewCell(mContext, resourcesProvider);
                    view = foldersPreviewCell;
                    break;
                case TYPE_FAB_SHAPE:
                    fabShapeCell = new FabShapeCell(mContext,
                            OpenExteraAppearanceActivity.this::rebuildAll);
                    fabShapeCell.setNeedDivider(true);
                    view = fabShapeCell;
                    break;
                case TYPE_SECTION_SLIDER:
                    AvatarCornersSeekBar slider = new AvatarCornersSeekBar(mContext,
                            OpenExteraAppearanceActivity.this::onSectionRadiusChanged,
                            0, AppearanceConfig.AVATAR_CORNERS_MAX,
                            getString(R.string.OEAppearanceSectionRadius),
                            getString(R.string.OEAppearanceSectionRadiusOff),
                            getString(R.string.OEAppearanceSectionRadiusMax));
                    slider.setValueSuffix("dp");
                    slider.setValue(AppearanceConfig.sectionRadius.Int());
                    slider.setBackgroundColor(getThemedColor(Theme.key_windowBackgroundWhite));
                    view = slider;
                    break;
                default:
                    return super.onCreateViewHolder(parent, viewType);
            }
            view.setLayoutParams(new RecyclerView.LayoutParams(
                    RecyclerView.LayoutParams.MATCH_PARENT, RecyclerView.LayoutParams.WRAP_CONTENT));
            return new RecyclerListView.Holder(view);
        }

        @Override
        public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            switch (holder.getItemViewType()) {
                case TYPE_HEADER: {
                    HeaderCell cell = (HeaderCell) holder.itemView;
                    if (position == avatarsHeaderRow) {
                        cell.setText(getString(R.string.FlexyMatteAvatars));
                    } else if (position == iconsHeaderRow) {
                        cell.setText(getString(R.string.FlexyMatteIcons));
                    } else if (position == appearanceHeaderRow) {
                        cell.setText(getString(R.string.FlexyMatteInterface));
                    } else if (position == sectionsHeaderRow) {
                        cell.setText(getString(R.string.OEAppearanceSections));
                    } else if (position == blurHeaderRow) {
                        cell.setText(getString(R.string.FlexyMatteEffects));
                    } else if (position == chatListHeaderRow) {
                        cell.setText(getString(R.string.OEAppearanceChatList));
                    } else if (position == foldersHeaderRow) {
                        cell.setText(getString(R.string.OEAppearanceFolders));
                    } else if (position == linksHeaderRow) {
                        cell.setText(getString(R.string.FlexyMatteNavigation));
                    }
                    break;
                }
                case TYPE_CHECK: {
                    TextCheckCell cell = (TextCheckCell) holder.itemView;
                    // Ячейки переиспользуются, поэтому «включённость» надо возвращать явно:
                    // иначе строка, побывавшая заблокированной, останется полупрозрачной.
                    cell.setEnabled(position != separateHeadersRow
                            || !AppearanceConfig.sectionsSeparatedHeadersForced(), null);
                    if (position == centerTitleRow) {
                        cell.setTextAndCheck(getString(R.string.OEAppearanceCenterTitle),
                                AppearanceConfig.INSTANCE.centerTitle(), true);
                    } else if (position == useSystemFontsRow) {
                        cell.setTextAndCheck(getString(R.string.OEAppearanceUseSystemFonts), NekoConfig.typeface.Bool(), true);
                    } else if (position == gooeyAvatarRow) {
                        cell.setTextAndCheck(getString(R.string.OEAppearanceGooeyAvatar), AppearanceConfig.gooeyAvatarAnimation.Bool(), true);
                    } else if (position == customThemesRow) {
                        cell.setTextAndCheck(getString(R.string.OEAppearanceCustomThemes), AppearanceConfig.customThemes.Bool(), false);
                    } else if (position == separateHeadersRow) {
                        cell.setTextAndCheck(getString(R.string.OEAppearanceSeparateHeaders), AppearanceConfig.sectionsSeparatedHeaders(), true);
                    } else if (position == glassMessageMenuRow) {
                        cell.setTextAndValueAndCheck(getString(R.string.OEAppearanceGlassMessageMenu), getString(R.string.OEAppearanceGlassMessageMenuInfo), AppearanceConfig.glassMessageMenu.Bool(), true, true);
                    } else if (position == forceBlurRow) {
                        cell.setTextAndCheck(getString(R.string.OEAppearanceForceBlur), LiteMode.isEnabledSetting(LiteMode.FLAG_CHAT_BLUR), true);
                    } else if (position == disableAvatarBlurRow) {
                        cell.setTextAndCheck(getString(R.string.OEAppearanceDisableAvatarBlur), NaConfig.INSTANCE.getDisableAvatarBlur().Bool(), false);
                    } else if (position == singleCornerRadiusRow) {
                        cell.setTextAndCheck(getString(R.string.OEAppearanceSingleCornerRadius), AppearanceConfig.singleCornerRadius.Bool(), false);
                    } else if (position == forceSnowRow) {
                        cell.setTextAndValueAndCheck(getString(R.string.OEAppearanceForceSnow), getString(R.string.OEAppearanceForceSnowInfo), NekoConfig.actionBarDecoration.Int() == 1, true, true);
                    } else if (position == folderThemeAccentRow) {
                        cell.setTextAndCheck(getString(R.string.FlexyFolderThemeAccent),AppearanceConfig.folderThemeAccent.Bool(),true);
                    } else if (position == senderMiniAvatarsRow) {
                        cell.setTextAndCheck(getString(R.string.OEAppearanceSenderMiniAvatars), AppearanceConfig.senderMiniAvatars.Bool(), false);
                    }
                    break;
                }
                case TYPE_SETTINGS: {
                    TextSettingsCell cell = (TextSettingsCell) holder.itemView;
                    if (position == dividerStyleRow) {
                        String[] v = {getString(R.string.OEAppearanceDividerHidden), getString(R.string.OEAppearanceDividerLine), getString(R.string.OEAppearanceDividerSegments)};
                        cell.setTextAndValue(getString(R.string.OEAppearanceDividerStyle), v[clamp(AppearanceConfig.dividerStyle.Int(), v.length)], false);
                    } else if (position == glassOutlineRow) {
                        String[] v = {getString(R.string.OEAppearanceGlassOutlineGlare), getString(R.string.OEAppearanceGlassOutlineSolid), getString(R.string.OEAppearanceGlassOutlineHidden)};
                        cell.setTextAndValue(getString(R.string.OEAppearanceGlassOutline), v[clamp(AppearanceConfig.glassOutlineStyle.Int(), v.length)], true);
                    } else if (position == tabTitleStyleRow) {
                        CharSequence[] v = tabTitleOptions();
                        cell.setTextAndValue(getString(R.string.OEAppearanceTabTitleStyle), v[tabTitleIndex(NekoConfig.tabsTitleType.Int())], true);
                    } else if (position == tabCounterRow) {
                        String[] v = {getString(R.string.OEAppearanceTabCounterAll),
                                getString(R.string.OEAppearanceTabCounterUnmuted),
                                getString(R.string.OEAppearanceTabCounterOff)};
                        cell.setTextAndValue(getString(R.string.OEAppearanceTabCounter), v[clamp(NaConfig.INSTANCE.getIgnoreUnreadCount().Int(), v.length)], false);
                    } else if (position == titleTextRow) {
                        CharSequence[] v = titleTextOptions();
                        int titleText = clamp(AppearanceConfig.titleText.Int(), v.length);
                        cell.setTextAndValue(getString(R.string.OEAppearanceTitleText),
                                titleText == AppearanceConfig.TITLE_TEXT_CUSTOM ? NaConfig.INSTANCE.getCustomTitle().String() : v[titleText], false);
                    }
                    break;
                }
                case TYPE_DETAIL_SETTINGS: {
                    // Иконка слева, подпись под заголовком.
                    TextDetailSettingsCell cell = (TextDetailSettingsCell) holder.itemView;
                    if (position == appNavigationRow) {
                        cell.setTextAndValueAndIcon(getString(R.string.OEAppearanceNavigation), getString(R.string.OEAppearanceNavigationSub), R.drawable.msg_newphone, true);
                    } else if(position==flexyShareRow){
                        cell.setTextAndValueAndIcon("Flexy Share Sheet",getString(R.string.FlexyShareEnabled),R.drawable.msg_share,true);
                    } else if (position == flexyLiquidNavigationRow) {
                        cell.setTextAndValueAndIcon(getString(R.string.FlexyLiquidNavTitle),
                            getString(R.string.FlexyLiquidNavPreview), R.drawable.msg_settings, true);
                    } else if (position == iconPacksRow) {
                        cell.setTextAndValueAndIcon(getString(R.string.OEAppearanceIconPacks), getString(R.string.OEAppearanceIconPacksInfo), R.drawable.msg_sticker, true);
                    } else if (position == emojiSetsRow) {
                        cell.setTextAndValueAndIcon(getString(R.string.EmojiSets), getString(NekoConfig.useSystemEmoji.Bool()
                                ? R.string.OEAppearanceUseSystemEmoji : R.string.OEAppearanceEmojiSetsInfo), R.drawable.msg_emoji_smiles, false);
                    } else if (position == pillStackRow) {
                        cell.setTextAndValueAndIcon(getString(R.string.OEAppearancePillStack), getString(R.string.OEAppearancePillStackInfo), R.drawable.outline_header_search, true);
                    } else if (position == hidingRow) {
                        cell.setTextAndValueAndIcon(getString(R.string.OEAppearanceHiding), getString(R.string.OEAppearanceHidingInfo), R.drawable.msg_archive_hide, false);
                    }
                    break;
                }
                case TYPE_INFO_PRIVACY: {
                    TextInfoPrivacyCell cell = (TextInfoPrivacyCell) holder.itemView;
                    // Скруглённый «хвост» списка положен последней тени, а она у нас после блока
                    // Blur, а не после строк-переходов.
                    boolean bottom = position == blurDividerRow;
                    if (position == appearanceDividerRow) {
                        cell.setText(getString(R.string.OEAppearanceCustomThemesInfo));
                    } else if (position == blurDividerRow) {
                        cell.setText(getString(R.string.OEAppearanceBlurInfo));
                    } else if (position == avatarsDividerRow) {
                        cell.setText(getString(R.string.OEAppearanceSingleCornerRadiusInfo));
                    } else if (position == chatListDividerRow) {
                        cell.setText(getString(R.string.OEAppearanceChatListInfo));
                    } else if (position == foldersDividerRow) {
                        cell.setText(getString(R.string.OEAppearanceFoldersInfo));
                    } else {
                        cell.setText(null);
                    }
                    cell.setBackground(Theme.getThemedDrawable(mContext,
                            bottom ? R.drawable.greydivider_bottom : R.drawable.greydivider,
                            Theme.key_windowBackgroundGrayShadow));
                    break;
                }
            }
        }

        @Override
        public int getItemViewType(int position) {
            if (position == avatarCornersPreviewRow) {
                return TYPE_AVATAR_CORNERS;
            } else if (position == chatListPreviewRow) {
                return TYPE_CHAT_LIST;
            } else if (position == foldersPreviewRow) {
                return TYPE_FOLDERS;
            } else if (position == sectionRadiusRow) {
                return TYPE_SECTION_SLIDER;
            } else if (position == appearanceHeaderRow || position == sectionsHeaderRow
                    || position == blurHeaderRow || position == chatListHeaderRow
                    || position == foldersHeaderRow || position == linksHeaderRow
                    || position == avatarsHeaderRow || position == iconsHeaderRow) {
                return TYPE_HEADER;
            } else if (position == appearanceDividerRow || position == sectionsDividerRow
                    || position == blurDividerRow || position == avatarsDividerRow
                    || position == chatListDividerRow || position == foldersDividerRow
                    || position == linksDividerRow || position == iconsDividerRow) {
                return TYPE_INFO_PRIVACY;
            } else if (position == fabShapeRow) {
                return TYPE_FAB_SHAPE;
            } else if (position == appNavigationRow || position == flexyLiquidNavigationRow || position == flexyShareRow || position == iconPacksRow
                    || position == emojiSetsRow || position == pillStackRow || position == hidingRow) {
                return TYPE_DETAIL_SETTINGS;
            } else if (position == dividerStyleRow || position == glassOutlineRow
                    || position == tabTitleStyleRow
                    || position == tabCounterRow || position == titleTextRow) {
                return TYPE_SETTINGS;
            }
            return TYPE_CHECK;
        }
    }

    private static int clamp(int value, int size) {
        if (value < 0) return 0;
        if (value >= size) return size - 1;
        return value;
    }

    @Override
    public void onResume() {
        super.onResume();
        AndroidUtilities.runOnUIThread(this::invalidatePreviews);
        if (foldersPreviewCell != null) {
            foldersPreviewCell.updateAllChatsTabName(false);
        }
        if (listAdapter != null && emojiSetsRow >= 0) {
            listAdapter.notifyItemChanged(emojiSetsRow);
        }
    }

    @Override
    public void onFragmentDestroy() {
        // Отложенная пересборка после слайдера радиуса переживёт закрытие экрана, если её не снять.
        AndroidUtilities.cancelRunOnUIThread(sectionRadiusRebuild);
        super.onFragmentDestroy();
    }
}
