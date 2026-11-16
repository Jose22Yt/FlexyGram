package org.telegram.lottie

import com.android.build.api.variant.AndroidComponentsExtension
import org.gradle.api.Plugin
import org.gradle.api.Project

class LottieMetaPlugin : Plugin<Project> {
    override fun apply(project: Project) {
        val extension = project.extensions.create("lottieMeta", LottieMetaExtension::class.java)
        extension.className.convention("ResLottieMeta")

        val androidComponents = project.extensions.findByType(AndroidComponentsExtension::class.java)
            ?: error("Apply com.android.application/library before org.telegram.lottie-meta")

        androidComponents.onVariants { variant ->
            val suffix = variant.name.replaceFirstChar { it.uppercase() }
            val task = project.tasks.register("generate${suffix}LottieMeta", LottieMetaTask::class.java) { task ->
                task.className.set(extension.className)
                task.packageName.set(extension.packageName.orElse(variant.namespace))
                task.rPackage.set(variant.namespace)

                variant.sources.res?.all?.let { layers ->
                    task.rawResources.from(
                        layers.map { collections ->
                            collections.flatten().map { directory ->
                                directory.asFileTree.matching { patterns -> patterns.include("raw*/**/*.json") }
                            }
                        }
                    )
                }
            }

            variant.sources.java?.addGeneratedSourceDirectory(task, LottieMetaTask::outputDir)
        }
    }
}
