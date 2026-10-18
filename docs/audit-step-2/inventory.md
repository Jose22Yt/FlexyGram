# Inventario estático verificable

[Índice](README.md). Superproyecto en `db1bea24b7b705de33f8ff8c8e174011c153cac7`. Los valores son declarados, no artefactos resueltos.

## Submódulos: URL y commit fijado

No se inicializaron. Las ramas declaradas no sustituyen el gitlink para reproducir una construcción. Los submódulos recursivos no están inventariados.

| Ruta | URL declarada | SHA del gitlink |
| --- | --- | --- |
| `TMessagesProj/jni/third_party/libvpx` | https://github.com/webmproject/libvpx.git | `1024874c5919305883187e2953de8fcb4c3d7fa6` |
| `TMessagesProj/jni/third_party/dav1d` | https://github.com/videolan/dav1d.git | `54706fc6bc0cdecab7e9593974a4039cc038fca7` |
| `TMessagesProj/jni/third_party/ffmpeg` | https://github.com/FFmpeg/FFmpeg.git | `45f1910444f34b02621f9f0426ea1a538a613c41` |
| `TMessagesProj/jni/third_party/xiph/ogg` | https://github.com/xiph/ogg.git | `be05b13e98b048f0b5a0f5fa8ce514d56db5f822` |
| `TMessagesProj/jni/third_party/xiph/opus` | https://github.com/xiph/opus.git | `22244de5a79bd1d6d623c32e72bf1954b56235be` |
| `TMessagesProj/jni/third_party/xiph/opusfile` | https://github.com/xiph/opusfile.git | `a55c164e9891a9326188b7d4d216ec9a88373739` |
| `TMessagesProj/lib/jlatexmath` | https://github.com/dkaraush/jlatexmath-android.git | `f59d6eecfac6fb58d6e3b7d6cff6c8aed9dbd5b4` |
| `TMessagesProj/jni/tlottie` | https://github.com/dkaraush/tlottie.git | `31f1b542f88e7b4be9a01e749920d857535fc715` |
| `TMessagesProj_Modules/media` | https://github.com/Arseny271/media.git | `c430d207677071b1873f9f18266d55ec45722180` |
| `TMessagesProj/jni/third_party/absl` | https://github.com/abseil/abseil-cpp.git | `54fac219c4ef0bc379dfffb0b8098725d77ac81b` |
| `TMessagesProj/jni/third_party/wamr` | https://github.com/wasm-micro-runtime/wasm-micro-runtime.git | `25bd7eb63e828e4bd242cc9b38d260b4b31c6605` |
| `TMessagesProj/jni/tgcalls` | https://github.com/TelegramMessenger/tgcalls.git | `ccbb57965020768c94f5b205ea08547a7e0fe49d` |
| `TMessagesProj/jni/wallet-engine` | https://github.com/dkaraush/wallet-engine.git | `5c65e47cb8d68727c20d89382d0bc51292486b9a` |
| `TMessagesProj/jni/third_party/boost-regex` | https://github.com/boostorg/regex.git | `4cbcd3078e6ae10d05124379623a1bf03fcb9350` |
| `TMessagesProj/jni/third_party/libprisma` | https://github.com/TelegramMessenger/libprisma.git | `31a5d6fbbef8136e4a2b3adaf7b95e2ccaa7436d` |
| `TMessagesProj/chaquopy` | https://github.com/exteraless/chaquopy.git | `d47b4a1e1817b4590b9c56dfd4ee5fcfdd6f0cbd` |

Fuente: [.gitmodules:L1](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.gitmodules#L1) y `git ls-tree -r db1bea24b7b705de33f8ff8c8e174011c153cac7` (modo 160000). Chaquopy declara además rama `exteraless`; se conserva el SHA fijado.

## Coordenadas Gradle literales

No incluye transitivas, versiones del AGP Kotlin integrado ni resolución del script media.

| Archivo / línea | Declaración |
| --- | --- |
| [build.gradle:L9](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L9) | `classpath 'com.android.tools.build:gradle:9.3.1'` |
| [build.gradle:L15](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L15) | `id 'com.google.gms.google-services' version '4.5.0' apply false` |
| [build.gradle:L16](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L16) | `id 'com.google.firebase.crashlytics' version '3.0.8' apply false` |
| [build.gradle:L17](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L17) | `id 'com.chaquo.python' version '17.0.0' apply false` |
| [build.gradle:L37](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L37) | `coreLibraryDesugaringEnabled = true` |
| [settings.gradle:L15](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/settings.gradle#L15) | `id 'org.gradle.toolchains.foojay-resolver-convention' version '1.0.0'` |
| [buildSrc/build.gradle.kts:L9](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/buildSrc/build.gradle.kts#L9) | `implementationClass = "org.telegram.lottie.LottieMetaPlugin"` |
| [buildSrc/build.gradle.kts:L21](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/buildSrc/build.gradle.kts#L21) | `implementation(gradleApi())` |
| [buildSrc/build.gradle.kts:L22](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/buildSrc/build.gradle.kts#L22) | `implementation("com.android.tools.build:gradle:9.3.1")` |
| [buildSrc/build.gradle.kts:L23](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/buildSrc/build.gradle.kts#L23) | `implementation("com.google.code.gson:gson:2.14.0")` |
| [TMessagesProj/build.gradle:L205](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L205) | `annotationProcessorOptions {` |
| [TMessagesProj/build.gradle:L372](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L372) | `implementation 'androidx.core:core-ktx:1.19.0'` |
| [TMessagesProj/build.gradle:L373](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L373) | `implementation 'androidx.palette:palette-ktx:1.0.0'` |
| [TMessagesProj/build.gradle:L374](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L374) | `implementation 'com.google.android.material:material:1.14.0'` |
| [TMessagesProj/build.gradle:L375](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L375) | `implementation 'androidx.exifinterface:exifinterface:1.4.2'` |
| [TMessagesProj/build.gradle:L376](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L376) | `implementation 'androidx.dynamicanimation:dynamicanimation:1.0.0'` |
| [TMessagesProj/build.gradle:L377](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L377) | `implementation 'androidx.mediarouter:mediarouter:1.8.1'` |
| [TMessagesProj/build.gradle:L378](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L378) | `implementation 'com.google.zxing:core:3.5.4'` |
| [TMessagesProj/build.gradle:L379](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L379) | `implementation 'com.neovisionaries:nv-websocket-client:2.14'` |
| [TMessagesProj/build.gradle:L380](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L380) | `implementation 'com.caverock:androidsvg-aar:1.4'` |
| [TMessagesProj/build.gradle:L381](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L381) | `implementation 'androidx.sharetarget:sharetarget:1.2.0'` |
| [TMessagesProj/build.gradle:L382](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L382) | `implementation 'androidx.interpolator:interpolator:1.0.0'` |
| [TMessagesProj/build.gradle:L383](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L383) | `implementation 'androidx.webkit:webkit:1.14.0'` |
| [TMessagesProj/build.gradle:L384](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L384) | `implementation 'androidx.biometric:biometric:1.1.0'` |
| [TMessagesProj/build.gradle:L385](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L385) | `implementation 'androidx.car.app:app:1.7.0'` |
| [TMessagesProj/build.gradle:L386](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L386) | `implementation 'androidx.car.app:app-projected:1.7.0'` |
| [TMessagesProj/build.gradle:L390](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L390) | `implementation 'androidx.camera:camera-core:1.6.2'` |
| [TMessagesProj/build.gradle:L391](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L391) | `implementation 'androidx.camera:camera-camera2:1.6.2'` |
| [TMessagesProj/build.gradle:L392](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L392) | `implementation 'androidx.camera:camera-lifecycle:1.6.2'` |
| [TMessagesProj/build.gradle:L393](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L393) | `implementation 'org.nanohttpd:nanohttpd:2.3.1'` |
| [TMessagesProj/build.gradle:L394](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L394) | `implementation 'com.alphacephei:vosk-android:0.3.75'` |
| [TMessagesProj/build.gradle:L395](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L395) | `compileOnly 'org.checkerframework:checker-qual:2.5.2'` |
| [TMessagesProj/build.gradle:L396](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L396) | `compileOnly 'org.checkerframework:checker-compat-qual:2.5.0'` |
| [TMessagesProj/build.gradle:L397](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L397) | `implementation 'com.google.firebase:firebase-messaging:25.1.2'` |
| [TMessagesProj/build.gradle:L398](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L398) | `implementation 'com.google.firebase:firebase-crashlytics:20.1.0'` |
| [TMessagesProj/build.gradle:L399](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L399) | `implementation 'com.google.android.gms:play-services-cast-framework:22.3.1'` |
| [TMessagesProj/build.gradle:L400](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L400) | `implementation 'com.google.android.gms:play-services-maps:20.0.0'` |
| [TMessagesProj/build.gradle:L401](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L401) | `implementation 'com.google.android.gms:play-services-auth:21.6.0'` |
| [TMessagesProj/build.gradle:L402](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L402) | `implementation 'com.google.android.gms:play-services-vision:20.1.3'` |
| [TMessagesProj/build.gradle:L403](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L403) | `implementation 'com.google.android.gms:play-services-wearable:20.0.1'` |
| [TMessagesProj/build.gradle:L404](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L404) | `implementation 'com.google.android.gms:play-services-location:21.4.0'` |
| [TMessagesProj/build.gradle:L405](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L405) | `implementation 'com.googlecode.mp4parser:isoparser:1.0.6'` |
| [TMessagesProj/build.gradle:L406](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L406) | `implementation 'com.google.mlkit:language-id:17.0.6'` |
| [TMessagesProj/build.gradle:L407](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L407) | `implementation 'com.google.code.gson:gson:2.14.0'` |
| [TMessagesProj/build.gradle:L408](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L408) | `implementation ('com.google.guava:guava:33.6.0-android') {` |
| [TMessagesProj/build.gradle:L416](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L416) | `implementation 'com.google.android.gms:play-services-mlkit-subject-segmentation:16.0.0-beta1'` |
| [TMessagesProj/build.gradle:L417](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L417) | `implementation 'com.google.android.gms:play-services-mlkit-image-labeling:16.0.8'` |
| [TMessagesProj/build.gradle:L418](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L418) | `implementation "androidx.credentials:credentials:1.6.0"` |
| [TMessagesProj/build.gradle:L419](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L419) | `implementation "androidx.credentials:credentials-play-services-auth:1.6.0"` |
| [TMessagesProj/build.gradle:L420](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L420) | `implementation "io.noties.markwon:core:4.6.2"` |
| [TMessagesProj/build.gradle:L421](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L421) | `implementation "io.noties.markwon:ext-strikethrough:4.6.2"` |
| [TMessagesProj/build.gradle:L422](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L422) | `implementation "io.noties.markwon:ext-tables:4.6.2"` |
| [TMessagesProj/build.gradle:L423](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L423) | `implementation "io.noties.markwon:html:4.6.2"` |
| [TMessagesProj/build.gradle:L424](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L424) | `implementation "io.noties.markwon:inline-parser:4.6.2"` |
| [TMessagesProj/build.gradle:L425](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L425) | `implementation "io.noties.markwon:ext-latex:4.6.2"` |
| [TMessagesProj/build.gradle:L427](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L427) | `implementation('com.stripe:stripe-android:2.0.2') {` |
| [TMessagesProj/build.gradle:L430](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L430) | `implementation 'com.android.billingclient:billing:7.1.1'` |
| [TMessagesProj/build.gradle:L431](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L431) | `coreLibraryDesugaring 'com.android.tools:desugar_jdk_libs_nio:2.1.5'` |
| [TMessagesProj/build.gradle:L434](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L434) | `implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.11.0'` |
| [TMessagesProj/build.gradle:L436](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L436) | `implementation 'org.osmdroid:osmdroid-android:6.1.20'` |
| [TMessagesProj/build.gradle:L438](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L438) | `implementation 'com.squareup.okhttp3:okhttp:5.5.0'` |
| [TMessagesProj/build.gradle:L439](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L439) | `implementation 'dnsjava:dnsjava:3.6.5'` |
| [TMessagesProj/build.gradle:L441](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L441) | `implementation 'com.jaredrummler:truetypeparser-light:1.0.0'` |
| [TMessagesProj/build.gradle:L443](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L443) | `implementation 'org.unifiedpush.android:connector:3.3.4'` |
| [TMessagesProj/build.gradle:L445](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L445) | `implementation 'androidx.room:room-runtime:2.8.4'` |
| [TMessagesProj/build.gradle:L446](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L446) | `annotationProcessor 'androidx.room:room-compiler:2.8.4'` |
| [TMessagesProj/build.gradle:L448](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L448) | `implementation 'org.apache.commons:commons-text:1.15.0'` |
| [TMessagesProj/build.gradle:L450](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L450) | `implementation 'app.nekogram.translator:translator:1.6.1'` |
| [TMessagesProj/build.gradle:L453](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L453) | `implementation 'com.aliucord:Aliuhook:1.1.4'` |
| [TMessagesProj/build.gradle:L454](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L454) | `implementation 'org.mvel:mvel2:2.5.2.Final'` |
| [TMessagesProj/build.gradle:L455](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L455) | `implementation 'com.linkedin.dexmaker:dexmaker:2.28.6'` |
| [TMessagesProj/build.gradle:L456](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L456) | `implementation 'org.lsposed.hiddenapibypass:hiddenapibypass:6.1'` |
| [TMessagesProj/build.gradle:L458](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L458) | `api project(":TMessagesProj_Modules:media3:media-lib-exoplayer")` |
| [TMessagesProj/build.gradle:L459](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L459) | `api project(":TMessagesProj_Modules:media3:media-lib-exoplayer-dash")` |
| [TMessagesProj/build.gradle:L460](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L460) | `api project(":TMessagesProj_Modules:media3:media-lib-exoplayer-hls")` |
| [TMessagesProj/build.gradle:L461](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L461) | `api project(":TMessagesProj_Modules:media3:media-lib-decoder-ffmpeg")` |
| [TMessagesProj/build.gradle:L462](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L462) | `api project(":TMessagesProj_Modules:media3:media-lib-session")` |
| [TMessagesProj/build.gradle:L464](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L464) | `compileOnly fileTree('libs')` |
| [TMessagesProj/build.gradle:L466](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L466) | `implementation files('libs/glyph-matrix-sdk-2.0.aar')` |

## Paquetes Python declarados en app

- `install 'beautifulsoup4'` — [TMessagesProj/build.gradle:L146](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L146)
- `install 'debugpy'` — [TMessagesProj/build.gradle:L147](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L147)
- `install 'lxml'` — [TMessagesProj/build.gradle:L148](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L148)
- `install 'packaging'` — [TMessagesProj/build.gradle:L149](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L149)
- `install 'pillow'` — [TMessagesProj/build.gradle:L150](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L150)
- `install 'requests'` — [TMessagesProj/build.gradle:L151](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L151)
- `install 'PyYAML'` — [TMessagesProj/build.gradle:L152](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L152)

## Prebuilts versionados

Esta lista registra presencia, tamaño y SHA de blob Git, no certifica compatibilidad ABI/ELF ni procedencia de compilación.

| Archivo | Bytes | SHA blob |
| --- | --- | --- |
| `TMessagesProj/jni/boringssl/lib/arm64-v8a/libcrypto.a` | 13107200 | `4dd195181ea76be56c3a1e2e97606cb89df592b9` |
| `TMessagesProj/jni/boringssl/lib/arm64-v8a/libssl.a` | 15012368 | `fa08ed0e24a473c75e2290106e95ed149ae174c8` |
| `TMessagesProj/jni/boringssl/lib/armeabi-v7a/libcrypto.a` | 9968450 | `e209a2d55f2dd173e249a699d5584278b1f744b7` |
| `TMessagesProj/jni/boringssl/lib/armeabi-v7a/libssl.a` | 11996990 | `dcfb506236edb99582c3bd05c3573854d786605e` |
| `TMessagesProj/jni/boringssl/lib/x86/libcrypto.a` | 9729548 | `fafb904d773fb6d6520b0badbf9121357cb0f6d3` |
| `TMessagesProj/jni/boringssl/lib/x86/libssl.a` | 11222050 | `4dfa9464724062c563486a5a99739d43d84d465b` |
| `TMessagesProj/jni/boringssl/lib/x86_64/libcrypto.a` | 13284166 | `7681f79fe6f963be6b2d92d69429416f5aafed8f` |
| `TMessagesProj/jni/boringssl/lib/x86_64/libssl.a` | 14831624 | `9c048ad94cf31b360b7f8fb5660ed8a4e0dd94f9` |
| `TMessagesProj/jni/boringssl/util/ar/testdata/linux/libsample.a` | 3328 | `cae6ae70c97f94667fb80becb0f420eccfa5d79b` |
| `TMessagesProj/jni/boringssl/util/ar/testdata/mac/libsample.a` | 1864 | `b7d8eb5ce0ff38cd7f9f1c5758ef4904865c4889` |
| `TMessagesProj/jni/ffmpeg/arm64-v8a/libavcodec.a` | 4228290 | `ef67ff4030f01682028f7076d527347a243cb191` |
| `TMessagesProj/jni/ffmpeg/arm64-v8a/libavformat.a` | 1214736 | `69c55c28a8ca4918ab01959990666e0230d68035` |
| `TMessagesProj/jni/ffmpeg/arm64-v8a/libavutil.a` | 1176652 | `acfddb049ac6ea1fa7d8f3bdc5558379b0778b87` |
| `TMessagesProj/jni/ffmpeg/arm64-v8a/libdav1d.a` | 1296618 | `b764a277d822e3b128efdebc274daea81f0b306d` |
| `TMessagesProj/jni/ffmpeg/arm64-v8a/libopus.a` | 743914 | `31648a719580d0b0eba43ca66b752240651f0589` |
| `TMessagesProj/jni/ffmpeg/arm64-v8a/libswresample.a` | 156122 | `8582cbd814bdcd1bdbfeb33032d1c1e0017934af` |
| `TMessagesProj/jni/ffmpeg/arm64-v8a/libswscale.a` | 1290228 | `a61daf685ca16fd2d487514f0c9304a58ef5f6fc` |
| `TMessagesProj/jni/ffmpeg/arm64-v8a/libvpx.a` | 2306414 | `387a148f7a4177defcaeee27511e2757dc1c47dd` |
| `TMessagesProj/jni/ffmpeg/armeabi-v7a/libavcodec.a` | 3340246 | `ef76dcf2e15a8ee9a3c3cc8fbed22cb12ad3cc86` |
| `TMessagesProj/jni/ffmpeg/armeabi-v7a/libavformat.a` | 960728 | `23c1b326978eade3d64e4a8fbead38d15cfff6ba` |
| `TMessagesProj/jni/ffmpeg/armeabi-v7a/libavutil.a` | 975738 | `b89cdd6a49857523d20341dc73b168abf8377135` |
| `TMessagesProj/jni/ffmpeg/armeabi-v7a/libdav1d.a` | 1097516 | `cc37fd94882253c11daab3a28ff7507a88758483` |
| `TMessagesProj/jni/ffmpeg/armeabi-v7a/libopus.a` | 596334 | `28187033dd5e82c221544a567d66d0163dac5a45` |
| `TMessagesProj/jni/ffmpeg/armeabi-v7a/libswresample.a` | 130514 | `1e77b7600e5cc0d28776e296dc45c0280c227366` |
| `TMessagesProj/jni/ffmpeg/armeabi-v7a/libswscale.a` | 1001652 | `d04a6e2f35c952e38945ecd668b50ea61d6f51b9` |
| `TMessagesProj/jni/ffmpeg/armeabi-v7a/libvpx.a` | 2431462 | `e615d79235676c11e4f2002b02251ac0b6717a2f` |
| `TMessagesProj/jni/ffmpeg/x86/libavcodec.a` | 2679864 | `6f8799d5947e7e83c5a806543f3cfdf382e994be` |
| `TMessagesProj/jni/ffmpeg/x86/libavformat.a` | 830352 | `452099fb8011da1bcda17d3e3a27e3e011b892a8` |
| `TMessagesProj/jni/ffmpeg/x86/libavutil.a` | 828138 | `eb0ae19912ee84641301cede03a1b3365a350bf4` |
| `TMessagesProj/jni/ffmpeg/x86/libdav1d.a` | 1529876 | `47f32d2f0b998f6ac3a8813f435f619b8933a195` |
| `TMessagesProj/jni/ffmpeg/x86/libopus.a` | 532512 | `6819db39ad0f67bbe32b95886648fa45f8cd0353` |
| `TMessagesProj/jni/ffmpeg/x86/libswresample.a` | 107426 | `1059602f662af75f6c830648a3710ac541f70213` |
| `TMessagesProj/jni/ffmpeg/x86/libswscale.a` | 894356 | `9a12db769d4c6be930b578be5b4f49fc277aa410` |
| `TMessagesProj/jni/ffmpeg/x86/libvpx.a` | 2792898 | `6e69d820cad20379b0276d8a6a0b9464f5212d12` |
| `TMessagesProj/jni/ffmpeg/x86_64/libavcodec.a` | 3260980 | `cd2cfc76403f9efc2ee36d8e77a4315e70cd6f72` |
| `TMessagesProj/jni/ffmpeg/x86_64/libavformat.a` | 1022264 | `d7df8f45434d62783e02514b2747c6a54d2e813b` |
| `TMessagesProj/jni/ffmpeg/x86_64/libavutil.a` | 1000126 | `4a1ec701b55f752108e50da04ae04664a7201dcc` |
| `TMessagesProj/jni/ffmpeg/x86_64/libdav1d.a` | 3255702 | `dfa645cd9f2c276d9a54a818d5ebd0db6eed0361` |
| `TMessagesProj/jni/ffmpeg/x86_64/libopus.a` | 644628 | `da6308d8bb2ab2f4540cc7b9af9393ba5ee60c0e` |
| `TMessagesProj/jni/ffmpeg/x86_64/libswresample.a` | 129642 | `8dc14907afee22b6a3ba2a97954cf96cf175e8f3` |
| `TMessagesProj/jni/ffmpeg/x86_64/libswscale.a` | 1065084 | `6d121913ce0ea02c45f84945adf3dfd33c2cf339` |
| `TMessagesProj/jni/ffmpeg/x86_64/libvpx.a` | 3101410 | `fca57c2856e435260bd026f9344853eedfeb7099` |
| `TMessagesProj/jni/prebuild/lib/arm64-v8a/libiwasm.a` | 1179024 | `3c030b130ca4c7506d7fc248f80f1491ffe12524` |
| `TMessagesProj/jni/prebuild/lib/arm64-v8a/libprisma.a` | 522092 | `6f9945bd182e3707c8ea3aaa1e2f9a730ca6eaef` |
| `TMessagesProj/jni/prebuild/lib/arm64-v8a/libwallet_engine.a` | 30309934 | `10fdbe5f377f1030cc38f00c2b5af4cc8dda4bd2` |
| `TMessagesProj/jni/prebuild/lib/armeabi-v7a/libiwasm.a` | 1106174 | `ba406c44d6a88bc072118a8414c72bfcf883272c` |
| `TMessagesProj/jni/prebuild/lib/armeabi-v7a/libprisma.a` | 465186 | `f0de871aaf5f25027f351673ce6435e8c1f331bf` |
| `TMessagesProj/jni/prebuild/lib/armeabi-v7a/libwallet_engine.a` | 26384044 | `c2681c8ed38980bb530019dfa0d16c525dc2fe72` |
| `TMessagesProj/jni/prebuild/lib/x86/libiwasm.a` | 894312 | `b1455ba1773345d15c540840c3c420010cbea6b8` |
| `TMessagesProj/jni/prebuild/lib/x86/libprisma.a` | 427518 | `85edb26a9c4c08887d27bae18a90e2aa9108a7fe` |
| `TMessagesProj/jni/prebuild/lib/x86/libwallet_engine.a` | 24629758 | `e832310966485044d47c93149c35f35df8a0be28` |
| `TMessagesProj/jni/prebuild/lib/x86_64/libiwasm.a` | 1193876 | `94d1d5e3c7554e3e6b974341f8cad2ed35dd613b` |
| `TMessagesProj/jni/prebuild/lib/x86_64/libprisma.a` | 531780 | `b479227ce14a38586c15f3410770ef253d0e3add` |
| `TMessagesProj/jni/prebuild/lib/x86_64/libwallet_engine.a` | 27248024 | `96dd4db77896a335497f10f448a520d09d1f76e4` |
| `TMessagesProj/jni/tde2e/arm64-v8a/libtde2e.a` | 20251980 | `a6f93c9d1c26239a761637601bc9e45c0d467790` |
| `TMessagesProj/jni/tde2e/arm64-v8a/libtdutils.a` | 20069460 | `22c8018e749e9dc139a4eca9fae946f2db58102d` |
| `TMessagesProj/jni/tde2e/armeabi-v7a/libtde2e.a` | 15748764 | `a1486caf635f8422fe536263fadf9ccab06aeb69` |
| `TMessagesProj/jni/tde2e/armeabi-v7a/libtdutils.a` | 14796366 | `f768e01d4f1c9841624ac2e4c59a244841ba91dd` |
| `TMessagesProj/jni/tde2e/x86/libtde2e.a` | 14286526 | `79ce669878055a0ac9cfb7bfefc75e0bc10eb842` |
| `TMessagesProj/jni/tde2e/x86/libtdutils.a` | 13993162 | `99be057c7d1aaca16b58829a1e0ec8690ba43495` |
| `TMessagesProj/jni/tde2e/x86_64/libtde2e.a` | 19500120 | `61e8a4d209de629811bd27f4c2544b926e54a0b5` |
| `TMessagesProj/jni/tde2e/x86_64/libtdutils.a` | 19573896 | `2b664b4cc36f0529813c991c5d03e8d765921832` |
| `TMessagesProj/jni/third_party/breakpad/src/third_party/linux/lib/gflags/libgflags.a` | 390804 | `c0de874c969cb05c58fa24af1293f65642b26dc0` |
| `TMessagesProj/jni/third_party/breakpad/src/third_party/linux/lib/glog/libglog.a` | 226928 | `8d2afaef645de7ae6ba30a1b855f75343f689383` |
| `TMessagesProj/jni/tlottie_lib/arm64-v8a/libtlottie.a` | 2903742 | `f47751c05b25a53a6a1507473e641b6eec4303e7` |
| `TMessagesProj/jni/tlottie_lib/armeabi-v7a/libtlottie.a` | 3007890 | `5acb7a424ad0baa81878398d344d485e033fcdeb` |
| `TMessagesProj/jni/tlottie_lib/x86/libtlottie.a` | 2934628 | `72d7fe0ee75ef68faa2d137c1311d70136a5c5c0` |
| `TMessagesProj/jni/tlottie_lib/x86_64/libtlottie.a` | 3198556 | `49c0f37a3a514c47b9e94dde8698930ee59c542b` |
| `TMessagesProj/libs/glyph-matrix-sdk-2.0.aar` | 58757 | `6d24fb81b5a72240a92b66fba0dd400eb04b9aa3` |

## Conteos por lenguaje y límites

| Extensión | Rutas |
| --- | --- |
| `.java` | 2696 |
| `.kt` | 60 |
| `.cpp` | 178 |
| `.c` | 296 |
| `.py` | 177 |
| `.xml` | 2116 |
| `.a` | 68 |
| `.aar` | 1 |

No equivalen a líneas revisadas. Se inventariaron todas las rutas; la lectura semántica se concentró en los símbolos enlazados en los demás informes. No se encontraron AGENTS.md, Gradle lockfiles ni verification-metadata.xml en este árbol. El grafo Media3, submódulos, fuentes generadas y dependencias de Maven/pip requieren validación posterior.
