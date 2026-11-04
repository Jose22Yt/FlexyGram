package app.flexygram.motionbuild

import com.android.build.api.instrumentation.AsmClassVisitorFactory
import com.android.build.api.instrumentation.ClassContext
import com.android.build.api.instrumentation.ClassData
import com.android.build.api.instrumentation.InstrumentationParameters
import com.android.build.api.instrumentation.InstrumentationScope
import com.android.build.api.instrumentation.FramesComputationMode
import com.android.build.api.variant.AndroidComponentsExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.objectweb.asm.ClassVisitor

class FastMotionPlugin : Plugin<Project> {
    override fun apply(project: Project) {
        val components = project.extensions.getByType(AndroidComponentsExtension::class.java)
        components.onVariants { variant ->
            variant.instrumentation.transformClassesWith(FastMotionFactory::class.java, InstrumentationScope.PROJECT) {}
            variant.instrumentation.setAsmFramesComputationMode(FramesComputationMode.COMPUTE_FRAMES_FOR_INSTRUMENTED_METHODS)
        }
    }
}

abstract class FastMotionFactory : AsmClassVisitorFactory<InstrumentationParameters.None> {
    override fun isInstrumentable(classData: ClassData): Boolean = !classData.className.startsWith("app.flexygram.animation.")
    override fun createClassVisitor(classContext: ClassContext, nextClassVisitor: ClassVisitor): ClassVisitor {
        val cache = HashMap<Pair<String, String>, Boolean>()
        return FastMotionVisitor(nextClassVisitor) { owner, base ->
            cache.getOrPut(owner to base) {
                val name = owner.replace('/', '.')
                name == base || classContext.loadClassData(name)?.superClasses?.contains(base) == true
            }
        }
    }
}
