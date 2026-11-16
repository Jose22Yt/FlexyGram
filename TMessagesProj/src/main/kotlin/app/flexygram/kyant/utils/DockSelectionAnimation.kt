// Local adaptation of Kyant's Apache-2.0 catalog interaction; no scale, velocity deformation or springs.
package app.flexygram.kyant.utils

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.IntSize
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

/** Bounded selector position and optical press tint. Jobs replace preceding work, never accumulate. */
class DockSelectionAnimation(
    private val animationScope: CoroutineScope,
    initialValue: Float,
    private val valueRange: ClosedFloatingPointRange<Float>,
    val onDragStopped: DockSelectionAnimation.() -> Unit,
    val onDrag: DockSelectionAnimation.(size: IntSize, dragAmount: Offset) -> Unit
) {
    private val position=Animatable(initialValue)
    private val press=Animatable(0f)
    private var positionJob: Job?=null
    private var pressJob: Job?=null
    val value: Float get()=position.value
    val targetValue: Float get()=position.targetValue
    val pressProgress: Float get()=press.value
    val modifier: Modifier=Modifier.pointerInput(Unit) {
        inspectDragGestures(
            onDragStart={ pressTo(1f) },
            onDragEnd={ onDragStopped();pressTo(0f) },
            onDragCancel={ onDragStopped();pressTo(0f) }
        ) { _, delta -> onDrag(size,delta) }
    }
    private fun pressTo(target: Float) {
        pressJob?.cancel()
        pressJob=animationScope.launch {press.animateTo(target,tween(120))}
    }
    fun updateValue(value: Float) {
        positionJob?.cancel()
        positionJob=animationScope.launch {position.snapTo(value.coerceIn(valueRange))}
    }
    fun animateToValue(value: Float) {
        positionJob?.cancel()
        positionJob=animationScope.launch {position.animateTo(value.coerceIn(valueRange),tween(160))}
    }
}
