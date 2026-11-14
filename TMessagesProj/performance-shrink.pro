# Runtime entry points used by Python, settings registries, presets and plugins.
# Preserve their public/reflective behavior while reducing unused dependency code.
-keep class app.flexygram.** { *; }
-keep class app.exteraless.** { *; }
-keep class org.telegram.messenger.R$* { *; }
-keepclasseswithmembers,includedescriptorclasses class * {
    native <methods>;
}
# JNI can also invoke ordinary Java callbacks on the same native bridge class.
-if class ** {
    native <methods>;
}
-keep,includedescriptorclasses class <1> { *; }
