package app.flexygram.kyant

import android.content.Context
import android.content.res.Configuration
import android.os.Build
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import androidx.annotation.RequiresApi
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.platform.AbstractComposeView
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.ViewCompositionStrategy
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.kyant.backdrop.backdrops.layerBackdrop
import com.kyant.backdrop.backdrops.rememberLayerBackdrop
import app.flexygram.kyant.components.LiquidBottomTab
import app.flexygram.kyant.components.LiquidBottomTabs
import org.telegram.messenger.LiteMode
import org.telegram.messenger.LocaleController
import org.telegram.ui.ActionBar.Theme
import org.telegram.ui.MainTabsLayout
import org.telegram.ui.Components.glass.GlassTabView

/** Original Kyant Compose material, mounted over a native dock with native actions and icons. */
@RequiresApi(33)
class KyantDockView(context: Context, private val dock: MainTabsLayout, scene: View) : AbstractComposeView(context) {
    private val source = KyantBackdropSource(scene, dock)
    private var tabs by mutableStateOf<List<GlassTabView>>(emptyList())
    private var selectedIndex by mutableIntStateOf(0)
    private var revision by mutableLongStateOf(0)
    private var iconsRevision by mutableLongStateOf(0)
    private var geometryRevision by mutableIntStateOf(0)
    private var available by mutableStateOf(true)
    private var ready = false
    private var framePending = false
    private var sourceDirty = false
    private var iconsDirty = false
    private var drawingIcon = false
    private var gesture = false
    private var downX = 0f
    private var downY = 0f
    private var downTime = 0L
    private var longPressTab: GlassTabView? = null
    private var longPressConsumed = false
    private val longPress = Runnable {
        if (gesture && isRendering() && longPressTab?.performLongClick() == true) {
            longPressConsumed = true
            val cancel = MotionEvent.obtain(downTime, android.os.SystemClock.uptimeMillis(), MotionEvent.ACTION_CANCEL, downX, downY, 0)
            super.dispatchTouchEvent(cancel)
            cancel.recycle()
        }
    }
    private val frame = Runnable {
        framePending = false
        val refreshNative = iconsDirty
        if (sourceDirty) { sourceDirty = false; revision++ }
        if (iconsDirty) { iconsDirty = false; iconsRevision++ }
        // Scrolling changes only the background layer; do not rebuild the tab list/composition.
        if (refreshNative) syncFromNative()
    }

    init {
        clipChildren = false
        clipToPadding = false
        setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnDetachedFromWindowOrReleasedFromPool)
    }

    fun isRendering(): Boolean = ready && available && isAttachedToWindow && tabs.size >= 2

    fun sourceInvalidated(target: View) {
        if (!source.isRecording && source.contains(target)) { sourceDirty = true; scheduleFrame() }
    }

    fun nativeIconsInvalidated() { if (!drawingIcon) { iconsDirty = true; scheduleFrame() } }
    fun backdropChanged() { sourceDirty = true; iconsDirty = true; scheduleFrame() }
    private fun scheduleFrame() {
        if (!framePending && isAttachedToWindow && windowVisibility == VISIBLE) {
            framePending = true; postOnAnimation(frame)
        }
    }

    fun syncFromNative() {
        val visible = (0 until dock.childCount).mapNotNull { dock.getChildAt(it) as? GlassTabView }
            .filter { dock.isViewVisible(it) && it.width > 0 }.sortedBy { it.x }
            .let { if (LocaleController.isRTL) it.reversed() else it }
        if (tabs != visible) tabs = visible
        if (visible.size < 2) ready = false
        val index = visible.indexOfFirst { it.isTabSelected }
        if (index >= 0 && selectedIndex != index) selectedIndex = index
        alpha = dock.alpha
        geometryRevision++
        dock.importantForAccessibility = if (ready && dock.visibility == VISIBLE && dock.alpha > 0f && !LiteMode.isPowerSaverApplied()) View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS else View.IMPORTANT_FOR_ACCESSIBILITY_AUTO
        available = dock.visibility == VISIBLE && dock.alpha > 0f && windowVisibility == VISIBLE && isHardwareAccelerated && !LiteMode.isPowerSaverApplied()
        if (!available) { removeCallbacks(longPress); gesture = false; longPressTab = null }
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        syncFromNative(); backdropChanged()
    }
    override fun onVisibilityAggregated(isVisible: Boolean) {
        super.onVisibilityAggregated(isVisible)
        available = isVisible && dock.visibility == VISIBLE && dock.alpha > 0f && isHardwareAccelerated && !LiteMode.isPowerSaverApplied()
        if (available) backdropChanged()
    }
    override fun onDetachedFromWindow() {
        removeCallbacks(longPress); longPressTab = null; gesture = false
        removeCallbacks(frame); framePending = false; source.release(); ready = false
        super.onDetachedFromWindow()
    }
    override fun dispatchTouchEvent(event: MotionEvent): Boolean {
        if (!isRendering()) return false
        val density = resources.displayMetrics.density
        val top = dock.y + (dock.height - 64 * density) / 2
        if (event.actionMasked == MotionEvent.ACTION_DOWN) {
            gesture = event.x >= dock.x && event.x < dock.x + dock.width && event.y >= top && event.y < top + 64 * density
        }
        if (!gesture) return false
        if (event.actionMasked == MotionEvent.ACTION_DOWN) {
            removeCallbacks(longPress)
            downX = event.x; downY = event.y; downTime = event.downTime; longPressConsumed = false
            val index = (((event.x - dock.x - 4 * density) / (dock.width - 8 * density).coerceAtLeast(1f)) * tabs.size).toInt().coerceIn(0, tabs.lastIndex)
            longPressTab = tabs[if (LocaleController.isRTL) tabs.lastIndex - index else index]
            postDelayed(longPress, ViewConfiguration.getLongPressTimeout().toLong())
        }
        if (event.actionMasked == MotionEvent.ACTION_MOVE) {
            val slop = ViewConfiguration.get(context).scaledTouchSlop
            if (kotlin.math.abs(event.x - downX) > slop || kotlin.math.abs(event.y - downY) > slop) removeCallbacks(longPress)
        }
        val handled = if (longPressConsumed) true else super.dispatchTouchEvent(event)
        if (event.actionMasked == MotionEvent.ACTION_UP || event.actionMasked == MotionEvent.ACTION_CANCEL) {
            gesture = false; removeCallbacks(longPress); longPressTab = null
        }
        return handled
    }

    @Composable override fun Content() {
        if (!available || tabs.size < 2) return
        geometryRevision // Layout/translation changes, never a continuous render ticker.
        val density = resources.displayMetrics.density
        val width = dock.width / density
        if (width <= 0) return
        val verticalInset = (dock.height - 64 * density) / 2
        val configuration = Configuration(LocalConfiguration.current).apply {
            uiMode = (uiMode and Configuration.UI_MODE_NIGHT_MASK.inv()) or
                if (Theme.isCurrentThemeDark()) Configuration.UI_MODE_NIGHT_YES else Configuration.UI_MODE_NIGHT_NO
        }
        val background = rememberLayerBackdrop()
        CompositionLocalProvider(
            LocalConfiguration provides configuration,
            LocalLayoutDirection provides if (LocaleController.isRTL) LayoutDirection.Rtl else LayoutDirection.Ltr
        ) {
            NativeDockBoundsLayout(dock.x.toInt(), (dock.y + verticalInset).toInt(), width) {
                // Match Kyant's hidden source-layer technique. The source contains only the native
                // page, so the dock can never capture itself or recursively sample its own glass.
                Canvas(Modifier.fillMaxSize().alpha(0f).layerBackdrop(background)) {
                    val currentRevision = revision
                    drawIntoCanvas { source.draw(it.nativeCanvas, dock.width, (64 * density).toInt(), currentRevision, verticalInset) }
                }
                key(tabs) {
                    LiquidBottomTabs(
                        selectedTabIndex = { selectedIndex },
                        onTabSelected = { index ->
                            tabs.getOrNull(index)?.let { if (!it.isTabSelected) it.performClick() }
                        },
                        backdrop = background,
                        tabsCount = tabs.size,
                        modifier = Modifier.fillMaxSize()
                    ) {
                        tabs.forEachIndexed { index, tab ->
                            LiquidBottomTab(
                                onClick = { selectedIndex = index },
                                modifier = Modifier.semantics {
                                    contentDescription = tab.contentDescription?.toString() ?: "Tab ${index + 1}"
                                    selected = index == selectedIndex
                                }
                            ) {
                                Canvas(Modifier.fillMaxSize()) {
                                    iconsRevision
                                    drawIntoCanvas { canvas ->
                                        val target = canvas.nativeCanvas
                                        val save = target.save()
                                        val scale = minOf(size.width / tab.width.coerceAtLeast(1), size.height / tab.height.coerceAtLeast(1))
                                        target.translate((size.width - tab.width * scale) / 2, (size.height - tab.height * scale) / 2)
                                        target.scale(scale, scale)
                                        drawingIcon = true
                                        try { tab.draw(target) } finally { drawingIcon = false }
                                        target.restoreToCount(save)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        SideEffect {
            if (!ready) { ready = true; dock.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS; dock.invalidate() }
        }
    }
}
