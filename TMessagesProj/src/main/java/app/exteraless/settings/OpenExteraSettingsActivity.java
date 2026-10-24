package app.exteraless.settings;

import static org.telegram.messenger.LocaleController.getString;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;


import androidx.recyclerview.widget.RecyclerView;

import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Components.RecyclerListView;

import tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity;
import tw.nekomimi.nekogram.ui.cells.HeaderCell;

/**
 * Корневой экран раздела exteraless.
 * Структура повторяет настройки exteraGram: About-шапка + категории с иконками.
 * Открывается из главных настроек (SettingsActivity, id 102).
 */
public class OpenExteraSettingsActivity extends BaseNekoSettingsActivity {

    private static final int MENU_CLOUD = 1;

    private static final int TYPE_ABOUT = 100;

    private int aboutRow;

    private int categoriesHeaderRow;
    private int generalRow;
    private int appearanceRow;
    private int chatsRow;
    private int flexyComposerRow;
    private int pluginsRow;
    private int otherRow;
    private int categoriesDividerRow;

    private int officialHeaderRow;
    private int channelRow;
    private int sourceRow;
    private int officialDividerRow;

    private int informationHeaderRow;
    private int aboutFlexyGramRow;
    private int creditsRow;
    private int informationDividerRow;

    @Override
    protected void updateRows() {
        super.updateRows();

        aboutRow = addRow("about");

        categoriesHeaderRow = addRow("categoriesHeader");
        generalRow = addRow("general");
        appearanceRow = addRow("appearance");
        chatsRow = addRow("chats");
        flexyComposerRow = addRow("flexyComposer");
        pluginsRow = addRow("plugins");
        otherRow = addRow("other");
        categoriesDividerRow = addRow();

        officialHeaderRow = addRow("flexyOfficialHeader");
        channelRow = addRow("flexyOfficialChannel");
        sourceRow = addRow("flexyOfficialSource");
        officialDividerRow = addRow();

        informationHeaderRow = addRow("flexyInformationHeader");
        aboutFlexyGramRow = addRow("flexyAbout");
        creditsRow = addRow("flexyCredits");
        informationDividerRow = addRow();
    }

    /**
     * У экстеры корневой экран устроен так: actionBar не занимает места и прозрачен,
     * пока список не прокручен, поэтому логотип стоит выше (в 12.9.0 верх логотипа
     * y=242 при низе actionBar 283). Заголовок проявляется вместе с фоном шапки.
     */
    @Override
    public View createView(Context context) {
        View view = super.createView(context);
        getMessagesController().getContentSettings(null);
        if (actionBar != null && fragmentView instanceof android.widget.FrameLayout) {
            // 1:1 с MainPreferencesActivity.createView из 12.9.0.
            actionBar.setBackground(null);
            actionBar.setCastShadows(false);
            actionBar.setAddToContainer(false);
            if (actionBar.getTitleTextView() != null) {
                actionBar.getTitleTextView().setAlpha(0f);
            }
            ((android.widget.FrameLayout) fragmentView).addView(actionBar,
                    org.telegram.ui.Components.LayoutHelper.createFrame(
                            org.telegram.ui.Components.LayoutHelper.MATCH_PARENT,
                            org.telegram.ui.Components.LayoutHelper.WRAP_CONTENT,
                            android.view.Gravity.TOP));
        }
        if (actionBar != null) {
            actionBar.createMenu().addItem(MENU_CLOUD, R.drawable.cloud_sync, getResourceProvider());
            actionBar.setActionBarMenuOnItemClick(new org.telegram.ui.ActionBar.ActionBar.ActionBarMenuOnItemClick() {
                @Override
                public void onItemClick(int id) {
                    if (id == -1) {
                        finishFragment();
                    } else if (id == MENU_CLOUD) {
                        presentFragment(new OpenExteraCloudActivity());
                    }
                }
            });
        }
        return view;
    }

    /**
     * Базовый класс в onInsets обнуляет верхний отступ списка. Нам он нужен: actionBar
     * прозрачный и не занимает места, поэтому без отступа контент уезжает под строку
     * состояния и логотип срезает.
     */
    /**
     * У экстеры на корневом экране адаптивный фон НЕ включается вовсе:
     * {@code BasePreferencesActivity.createView} вызывает {@code setAdaptiveBackground}
     * только при {@code !hasHeaderCell()}, а у {@code MainPreferencesActivity}
     * {@code hasHeaderCell()} возвращает true. Шапка остаётся прозрачной всегда,
     * заголовок не проявляется даже при прокрутке.
     */
    @Override
    protected void setupAdaptiveBackground() {
    }

    /** Блюр-подложка NagramX закрывает верх логотипа; у экстеры её нет. */
    @Override
    protected boolean needActionBarBlur() {
        return false;
    }

    @Override
    public void onInsets(int left, int top, int right, int bottom) {
        if (listView != null) {
            listView.setPadding(0, top, 0, bottom);
            listView.setClipToPadding(false);
        }
    }

    @Override
    protected String getActionBarTitle() {
        return getString(R.string.FlexyBrandName);
    }

    @Override
    public int getSearchGuid() {
        return 24000;
    }

    @Override
    public int getSearchIcon() {
        return R.drawable.msg_settings_old;
    }

    @Override
    public String getSearchPrefix() {
        return "OpenExtera";
    }

    @Override
    protected String getKey() {
        return "exteraless";
    }

    @Override
    protected BaseListAdapter createAdapter(Context context) {
        return new ListAdapter(context);
    }

    @Override
    protected void onItemClick(View view, int position, float x, float y) {
        if (position == generalRow) {
            presentFragment(new OpenExteraGeneralActivity());
        } else if (position == appearanceRow) {
            presentFragment(new OpenExteraAppearanceActivity());
        } else if (position == chatsRow) {
            presentFragment(new OpenExteraChatsActivity());
        } else if (position == flexyComposerRow) {
            presentFragment(new app.flexygram.composer.FlexyComposerSettingsActivity());
        } else if (position == pluginsRow) {
            presentFragment(new app.exteraless.plugins.ui.PluginsActivity());
        } else if (position == otherRow) {
            presentFragment(new OpenExteraOtherActivity());
        } else if (position == sourceRow) {
            org.telegram.messenger.browser.Browser.openUrl(getParentActivity(),
                    "https://github.com/Jose22Yt/FlexyGram");
        } else if (position == aboutFlexyGramRow) {
            showFlexyAbout();
        } else if (position == creditsRow) {
            showFlexyCredits();
        }
    }

    private void showFlexyAbout() {
        if (getParentActivity() == null) {
            return;
        }
        AlertDialog.Builder builder = new AlertDialog.Builder(getParentActivity(), getResourceProvider());
        builder.setTitle(getString(R.string.FlexySettingsAbout));
        builder.setMessage(getString(R.string.FlexySettingsAboutBody));
        builder.setPositiveButton(getString(R.string.OpenExteraSource), (dialog, which) ->
                org.telegram.messenger.browser.Browser.openUrl(getParentActivity(),
                        "https://github.com/Jose22Yt/FlexyGram"));
        builder.setNegativeButton(getString(R.string.OK), null);
        showDialog(builder.create());
    }

    private void showFlexyCredits() {
        if (getParentActivity() == null) {
            return;
        }
        AlertDialog.Builder builder = new AlertDialog.Builder(getParentActivity(), getResourceProvider());
        builder.setTitle(getString(R.string.FlexySettingsCredits));
        builder.setMessage(getString(R.string.FlexySettingsCreditsBody));
        builder.setPositiveButton(getString(R.string.FlexySettingsLicenseAction), (dialog, which) ->
                org.telegram.messenger.browser.Browser.openUrl(getParentActivity(),
                        "https://github.com/Jose22Yt/FlexyGram/blob/main/LICENSE"));
        builder.setNeutralButton(getString(R.string.FlexySettingsUpstreamAction), (dialog, which) ->
                org.telegram.messenger.browser.Browser.openUrl(getParentActivity(),
                        "https://github.com/exteraless/exteraless"));
        builder.setNegativeButton(getString(R.string.OK), null);
        showDialog(builder.create());
    }

    private class ListAdapter extends BaseListAdapter {

        public ListAdapter(Context context) {
            super(context);
        }

        @Override
        public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
            if (viewType == TYPE_ABOUT) {
                AboutHeaderCell view = new AboutHeaderCell(mContext);
                view.setOnLogoClickListener(v -> showDialog(new app.exteraless.updater.UpdaterSheet(OpenExteraSettingsActivity.this)));
                // У экстеры шапка лежит на фоне окна, а не в карточке-секции.
                view.setTag(RecyclerListView.TAG_NOT_SECTION);
                view.setLayoutParams(new RecyclerView.LayoutParams(
                        RecyclerView.LayoutParams.MATCH_PARENT, RecyclerView.LayoutParams.WRAP_CONTENT));
                return new RecyclerListView.Holder(view);
            }
            return super.onCreateViewHolder(parent, viewType);
        }

        @Override
        public void onBindViewHolder(RecyclerView.ViewHolder holder, int position, boolean partial) {
            switch (holder.getItemViewType()) {
                case TYPE_HEADER: {
                    HeaderCell cell = (HeaderCell) holder.itemView;
                    if (position == informationHeaderRow) {
                        cell.setText(getString(R.string.FlexySettingsInformation));
                    } else if (position == categoriesHeaderRow) {
                        cell.setText(getString(R.string.OpenExteraCategories));
                    } else if (position == officialHeaderRow) {
                        cell.setText(getString(R.string.FlexySettingsOfficial));
                    }
                    break;
                }
                case TYPE_TEXT: {
                    TextCell cell = (TextCell) holder.itemView;
                    if (position == generalRow) {
                        cell.setTextAndIcon(getString(R.string.OpenExteraGeneral), R.drawable.msg_media, true);
                    } else if (position == appearanceRow) {
                        cell.setTextAndIcon(getString(R.string.OpenExteraAppearance), R.drawable.msg_theme, true);
                    } else if (position == chatsRow) {
                        cell.setTextAndIcon(getString(R.string.OpenExteraChats), R.drawable.msg_discussion, true);
                    } else if (position == flexyComposerRow) {
                        cell.setTextAndIcon(getString(R.string.FlexySettingsComposerRow), R.drawable.msg_discussion, true);
                    } else if (position == pluginsRow) {
                        cell.setTextAndIcon(getString(R.string.OpenExteraPlugins), R.drawable.msg_plugins, true);
                    } else if (position == otherRow) {
                        cell.setTextAndIcon(getString(R.string.OpenExteraOther), R.drawable.msg_fave, false);
                    } else if (position == channelRow) {
                        // No official channel address has been announced; never forward to upstream.
                        cell.setTextAndValueAndIcon(getString(R.string.FlexySettingsOfficialChannel),
                                getString(R.string.FlexySettingsComingSoon), R.drawable.msg_channel, true);
                    } else if (position == sourceRow) {
                        cell.setTextAndValueAndIcon(getString(R.string.OpenExteraSource),
                                getString(R.string.FlexyBrandName), R.drawable.msg_language, false);
                    } else if (position == aboutFlexyGramRow) {
                        cell.setTextAndIcon(getString(R.string.FlexySettingsAbout),
                                R.drawable.msg_language, true);
                    } else if (position == creditsRow) {
                        cell.setTextAndIcon(getString(R.string.FlexySettingsCredits),
                                R.drawable.msg_fave, false);
                    }
                    // ВАЖНО: только после setTextAndIcon* — они сбрасывают imageLeft в 16dp.
                    // Метрики сняты с 12.9.0 (420 dpi): иконка 88px от края экрана, текст 219px,
                    // то есть 21dp и 71dp вместо дефолтных 16dp и 58dp.
                    cell.setImageLeft(21);
                    cell.setOffsetFromImage(71);
                    break;
                }
                case TYPE_INFO_PRIVACY: {
                    TextInfoPrivacyCell cell = (TextInfoPrivacyCell) holder.itemView;
                    if (position == informationDividerRow) {
                        cell.setText(null);
                        cell.setBackground(Theme.getThemedDrawable(mContext,
                                R.drawable.greydivider_bottom, Theme.key_windowBackgroundGrayShadow));
                    }
                    break;
                }
            }
        }

        @Override
        public boolean isEnabled(RecyclerView.ViewHolder holder) {
            return holder.getItemViewType() == TYPE_TEXT
                    && holder.getAdapterPosition() != channelRow;
        }

        @Override
        public int getItemViewType(int position) {
            if (position == aboutRow) {
                return TYPE_ABOUT;
            } else if (position == categoriesHeaderRow || position == officialHeaderRow
                    || position == informationHeaderRow) {
                return TYPE_HEADER;
            } else if (position == categoriesDividerRow || position == officialDividerRow) {
                // Промежуток между секциями — тень фиксированной высоты. TextInfoPrivacyCell
                // здесь держал высоту под подпись, которой нет, и оставлял пустое поле.
                return TYPE_SHADOW;
            } else if (position == informationDividerRow) {
                return TYPE_INFO_PRIVACY;
            }
            return TYPE_TEXT;
        }
    }
}
