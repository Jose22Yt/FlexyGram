package app.flexygram.kyant

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.absoluteOffset
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.AbsoluteAlignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp

/** Native View coordinates are physical; only the tab contents use the locale's direction. */
@Composable
internal fun NativeDockBoundsLayout(x: Int, y: Int, widthDp: Float, content: @Composable BoxScope.() -> Unit) {
    // Drop the Android MATCH_PARENT minimum constraints before sizing the actual glass panel.
    Box(Modifier.fillMaxSize()) {
        Box(
            Modifier.align(AbsoluteAlignment.TopLeft)
                .absoluteOffset { IntOffset(x, y) }
                .size(widthDp.dp, 64.dp),
            content = content
        )
    }
}
