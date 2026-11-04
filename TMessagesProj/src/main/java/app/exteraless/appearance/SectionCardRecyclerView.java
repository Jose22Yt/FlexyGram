package app.exteraless.appearance;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.RectF;
import java.util.Objects;
import app.flexygram.settings.signature.SettingsCardStyle;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.BlurredRecyclerView;
import org.telegram.ui.Components.RecyclerListView;

/** Settings-only segmented cards. Native section grouping, clipping, touch and scrolling remain owners. */
public class SectionCardRecyclerView extends BlurredRecyclerView {
    private final app.flexygram.settings.signature.SettingsCardBackground cardBackground = new app.flexygram.settings.signature.SettingsCardBackground();

    public SectionCardRecyclerView(Context context) {
        super(context);
        setForceSegmentedSettingsCards(true);
    }
    public void setCardResourcesProvider(Theme.ResourcesProvider provider) { cardBackground.setResourcesProvider(provider); invalidate(); }
    /** Source-compatible legacy hook. Grouped settings now use flat opaque cards. */
    public void setForceShadows(boolean value) {}

    @Override public void setSections(int padding, float radius, boolean topPadding) {
        setSections(view -> !(view instanceof org.telegram.ui.Cells.TextInfoPrivacyCell
                || view instanceof org.telegram.ui.Cells.ShadowSectionCell
                || view instanceof org.telegram.ui.Cells.GraySectionCell
                || view instanceof org.telegram.ui.Cells.HeaderCell
                || view instanceof tw.nekomimi.nekogram.ui.cells.HeaderCell)
                && !Objects.equals(view.getTag(), RecyclerListView.TAG_NOT_SECTION),
            type -> getAdapter() instanceof app.flexygram.settings.signature.SettingsSectionTypes
                && ((app.flexygram.settings.signature.SettingsSectionTypes)getAdapter()).isSettingsContentType(type),
            AndroidUtilities.dp(SettingsCardStyle.INSET), AndroidUtilities.dp(SettingsCardStyle.OUTER_RADIUS),
            this::drawBackgroundRect, topPadding);
    }

    @Override public void drawBackgroundRect(Canvas canvas, RectF rect, float topRadius, float bottomRadius, float alpha) {
        cardBackground.draw(canvas,rect,topRadius,bottomRadius,alpha);
    }
}
