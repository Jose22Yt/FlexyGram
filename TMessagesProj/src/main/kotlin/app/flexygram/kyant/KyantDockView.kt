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
import app.flexygram.effects.ChatEdgeStyle
import app.flexygram.kyant.components.LiquidBottomTab
import app.flexygram.kyant.components.LiquidBottomTabs
import org.telegram.messenger.Utilities
import org.telegram.messenger.LiteMode
import org.telegram.messenger.LocaleController
import org.telegram.ui.ActionBar.Theme
import org.telegram.ui.MainTabsLayout
import org.telegram.ui.Components.glass.GlassTabView

/** Original Kyant Compose material, mounted over a native dock with native actions and icons. */
@RequiresApi(33)
class KyantDockView(context: Context, private val dock: MainTabsLayout, private val scene: View) : AbstractComposeView(context) {
    private val powerListener = Utilities.Callback<Boolean> { syncFromNative(); backdropChanged(); dock.invalidate() }
    private val configListener = Runnable { syncFromNative(); backdropChanged(); dock.invalidate() }
    private val iconSnapshots = java.util.IdentityHashMap<GlassTabView, KyantIconSnapshot>()
    private val visibleScratch = ArrayList<GlassTabView>(8)
    private val tabOrder = Comparator<GlassTabView> { a, b -> a.x.compareTo(b.x) }
    private val targetMatrix = android.graphics.Matrix()
    private val targetBounds = android.graphics.RectF()
    private val source = KyantBackdropSource(scene, dock)
    private var tabs by mutableStateOf<List<GlassTabView>>(emptyList())
    private var selectedIndex by mutableIntStateOf(0)
    private var revision by mutableLongStateOf(0)
    private var iconsRevision by mutableLongStateOf(0)
    private var geometryRevision by mutableIntStateOf(0)
    private val geometry = KyantDockGeometry.State()
    private var available by mutableStateOf(false)
    private var subtleEdge by mutableStateOf(false)
    private var satinEdge by mutableStateOf(false)
    private var colorOsGlassEdge by mutableStateOf(false)
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

    private fun mayIntersectDock(target: View): Boolean {
        if (target === scene || dock.width <= 0 || dock.height <= 0
                || target.width <= 0 || target.height <= 0
                || !target.isAttachedToWindow || !dock.isAttachedToWindow) {
            return true
        }
        targetMatrix.reset()
        target.transformMatrixToGlobal(targetMatrix)
        dock.transformMatrixToLocal(targetMatrix)
        targetBounds.set(0f, 0f, target.width.toFloat(), target.height.toFloat())
        targetMatrix.mapRect(targetBounds)
        val density = resources.displayMetrics.density
        val bandHeight = 64f * density
        val verticalInset = KyantDockGeometry.panelInset(dock.height, dock.paddingTop, dock.paddingBottom, bandHeight)
        val margin = 32f * density
        return targetBounds.right > -margin
            && targetBounds.left < dock.width + margin
            && targetBounds.bottom > verticalInset - margin
            && targetBounds.top < verticalInset + bandHeight + margin
    }

    fun sourceInvalidated(target: View) {
        if (available && !sourceDirty && !source.isRecording && source.contains(target) && mayIntersectDock(target)) {
            sourceDirty = true; scheduleFrame()
        }
    }

    fun nativeIconsInvalidated() { if (available && !drawingIcon) { iconsDirty = true; scheduleFrame() } }
    fun backdropChanged() { sourceDirty = true; iconsDirty = true; scheduleFrame() }
    private fun scheduleFrame() {
        if (available && !framePending && isAttachedToWindow && isShown && windowVisibility == VISIBLE) {
            framePending = true; postOnAnimation(frame)
        }
    }

    fun syncFromNative() {
        val wasRendering = isRendering()
        val wasAvailable = available
        available = isAttachedToWindow && windowVisibility == VISIBLE && isShown && dock.isShown &&
            dock.alpha > 0f && isHardwareAccelerated && KyantDockConfig.isEnabled() &&
            !LiteMode.isPowerSaverApplied() && !LiteMode.isThermalPressureHigh()
        if (!available) {
            if (wasAvailable) {
                ready = false
                removeCallbacks(longPress); gesture = false; longPressTab = null
                removeCallbacks(frame); framePending = false
                source.release()
                iconSnapshots.values.forEach { it.release() }
                iconSnapshots.clear()
                if (wasRendering) tabs.forEach { it.setSkipDrawSelector(false) }
                dock.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_AUTO
                dock.invalidate()
            }
            return
        }

        subtleEdge = ChatEdgeStyle.isSubtle()
        satinEdge = ChatEdgeStyle.isSatin()
        colorOsGlassEdge = ChatEdgeStyle.isColorOsGlass()
        visibleScratch.clear()
        for (i in 0 until dock.childCount) {
            val tab = dock.getChildAt(i) as? GlassTabView ?: continue
            if (dock.isViewVisible(tab) && tab.width > 0) visibleScratch.add(tab)
        }
        visibleScratch.sortWith(tabOrder)
        if (LocaleController.isRTL) visibleScratch.reverse()
        val visible = visibleScratch
        if (tabs != visible) {
            if (wasRendering) tabs.forEach { it.setSkipDrawSelector(false) }
            iconSnapshots.values.forEach { it.release() }
            iconSnapshots.clear()
            tabs = visible.toList()
        }
        if (visible.size < 2) ready = false
        val index = visible.indexOfFirst { it.isTabSelected }
        if (index >= 0 && selectedIndex != index) selectedIndex = index
        alpha = dock.alpha
        if (geometry.update(dock.x - x, dock.y - y, dock.width, dock.height, dock.paddingTop, dock.paddingBottom,
                LocaleController.isRTL, Theme.isCurrentThemeDark())) geometryRevision++
        val importance = if (isRendering()) View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS
            else View.IMPORTANT_FOR_ACCESSIBILITY_AUTO
        if (dock.importantForAccessibility != importance) dock.importantForAccessibility = importance
        if (ready) visible.forEach { it.setSkipDrawSelector(true) }
        if (!wasAvailable) backdropChanged()
        if (wasRendering != isRendering()) dock.invalidate()
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        LiteMode.addOnPowerSaverAppliedListener(powerListener)
        KyantDockConfig.addListener(configListener)
        syncFromNative(); backdropChanged()
    }
    override fun onVisibilityAggregated(isVisible: Boolean) {
        super.onVisibilityAggregated(isVisible)
        syncFromNative()
        if (available) backdropChanged()
    }
    override fun onDetachedFromWindow() {
        available = false
        LiteMode.removeOnPowerSaverAppliedListener(powerListener)
        KyantDockConfig.removeListener(configListener)
        iconSnapshots.values.forEach { it.release() }
        iconSnapshots.clear()
        tabs.forEach { it.setSkipDrawSelector(false) }
        dock.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_AUTO
        removeCallbacks(longPress); longPressTab = null; gesture = false
        removeCallbacks(frame); framePending = false; source.release(); ready = false
        super.onDetachedFromWindow()
    }
    override fun dispatchTouchEvent(event: MotionEvent): Boolean {
        if (!isRendering()) return false
        val density = resources.displayMetrics.density
        val left = dock.x - x
        val top = dock.y - y + KyantDockGeometry.panelInset(dock.height, dock.paddingTop, dock.paddingBottom, 64 * density)
        if (event.actionMasked == MotionEvent.ACTION_DOWN) {
            gesture = event.x >= left && event.x < left + dock.width && event.y >= top && event.y < top + 64 * density
        }
        if (!gesture) return false
        if (event.actionMasked == MotionEvent.ACTION_DOWN) {
            removeCallbacks(longPress)
            downX = event.x; downY = event.y; downTime = event.downTime; longPressConsumed = false
            val index = (((event.x - left - 4 * density) / (dock.width - 8 * density).coerceAtLeast(1f)) * tabs.size).toInt().coerceIn(0, tabs.lastIndex)
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
        val verticalInset = KyantDockGeometry.panelInset(dock.height, dock.paddingTop, dock.paddingBottom, 64 * density)
        val baseConfiguration = LocalConfiguration.current
        val darkTheme = Theme.isCurrentThemeDark()
        val configuration = remember(baseConfiguration, darkTheme) {
            Configuration(baseConfiguration).apply {
                uiMode = (uiMode and Configuration.UI_MODE_NIGHT_MASK.inv()) or
                    if (darkTheme) Configuration.UI_MODE_NIGHT_YES else Configuration.UI_MODE_NIGHT_NO
            }
        }
        val background = rememberLayerBackdrop()
        CompositionLocalProvider(
            LocalConfiguration provides configuration,
            LocalLayoutDirection provides if (LocaleController.isRTL) LayoutDirection.Rtl else LayoutDirection.Ltr
        ) {
            NativeDockBoundsLayout((dock.x - x).toInt(), (dock.y - y + verticalInset).toInt(), width) {
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
                        subtleEdge = subtleEdge,
                        satinEdge = satinEdge,
                        colorOsGlassEdge = colorOsGlassEdge,
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
                                        try { iconSnapshots.getOrPut(tab) { KyantIconSnapshot(tab) }.draw(target, iconsRevision) } finally { drawingIcon = false }
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
            if (available && tabs.size >= 2 && !ready) {
                ready = true
                tabs.forEach { it.setSkipDrawSelector(true) }
                dock.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS
                dock.invalidate()
            }
        }
    }
}
