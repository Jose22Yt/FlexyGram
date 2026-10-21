# realAlpha P1/P2 — corrección de Atrás y revisión Glyph

Base: PR #34, `36e27309bee4e6c27e3850321fa0c6c44e2acf42`. Rama independiente; no modificar ni fusionar PR #34, main o develop. La APK unsigned anterior se conserva como artefacto distinto.

## Corrección de producción

Se retiran de RealAlphaActivity el campo RealAlphaBack, su registro tras `super.onCreate(null)` y su override redundante de onDestroy. Se elimina RealAlphaBack.java. LaunchActivity y DialogsActivity permanecen byte a byte como en la base de PR #34; no se añade un motor de navegación ni se cambia la implementación original de gestos.

| API | Propietario tras la corrección | Validación disponible |
|---|---|---|
| 24–32 | onBackPressed y ciclo de vida heredados de LaunchActivity; el subclass no usa android.window | Fuente original sin cambios y pruebas del wrapper con dobles para cada API |
| 33 | OnBackInvokedCallback original de LaunchActivity | Un registro del superclass en el doble; despacho consecutivo y limpieza sin override |
| 34+ | OnBackAnimationCallback original de LaunchActivity | No se sustituye su instancia en el doble; cancelación y despacho consecutivo; gesto real pendiente |

Android documenta que, con la misma prioridad, se atienden los callbacks en orden inverso al registro: [OnBackInvokedDispatcher](https://developer.android.com/reference/android/window/OnBackInvokedDispatcher). El puente de realAlpha se registraba después del original, pudiendo desplazar la ruta predictiva/cajón de LaunchActivity. La corrección elimina ese segundo propietario.

## Pruebas y alcance

El harness compila el subclass real y sus políticas con JDK21/`--release 8`, usando dobles Android/controladores explícitos. Las regresiones verifican 14 niveles API (24–37): cero registros nuevos bajo 33, un registro del superclass a partir de 33, identidad del callback original, cinco despachos, cancelación simulada en 34+ y limpieza/recreación. Los nuevos tests rechazan las fuentes sin corregir de PR #34 en API33 y API34: dos fallos esperados y cero errores del harness.

Suite realAlpha actual: 56 pruebas distintas (39 runtime/wrappers, ocho perfiles y nueve del verificador APK), aprobadas en modo normal y `-O`. Tras endurecer el control DEX se repitieron únicamente sus nueve tests en ambos modos. No se suman esas repeticiones a los 56. Dos regresiones críticas existentes RPC/C++ se ejecutaron además, aprobadas. La prueba C++ necesitó añadir el CMake ya verificado al PATH; no se modificó la prueba para hacerla pasar.

Los controles de fuente existentes comparan LaunchActivity con la base original (solo el hook protegido de PR #34), ApplicationLoader/DialogsActivity y políticas offline byte a byte. El verificador realAlpha exige en DEX los callbacks originales de LaunchActivity, la ausencia del puente eliminado y de overrides de Atrás/destrucción en el subclass, además del factory real DialogsActivity. No se relajan los verificadores Diagnostic/Beta.

**Ninguna prueba host ejecuta ART, dibuja DialogsActivity ni certifica gestos físicos.** La matriz Android y el procedimiento del teléfono permanecen pendientes de ejecución; ver [PHONE-VALIDATION.md](PHONE-VALIDATION.md).

## Dependencia Glyph exacta

| Campo | Resultado estático |
|---|---|
| Archivo de dependencia local | `TMessagesProj/libs/glyph-matrix-sdk-2.0.aar` |
| Referencia Gradle | `implementation files('libs/glyph-matrix-sdk-2.0.aar')` |
| Bytes / SHA-256 | 58.757 / `be00ee9cd7115f6b11984c6e31fe98e298fb726940d1555063610685ef3bbf29` |
| Blob Git | `6d24fb81b5a72240a92b66fba0dd400eb04b9aa3` |
| Manifest package / mínimo declarado | `com.nothing.thirdparty` / API 33 |
| Metadatos AAR | minCompileSdk 1; coreLibraryDesugaringEnabled false; no contradicen ni sustituyen minSdk 33 |
| classes.jar SHA-256 | `6337768b9b07e21072054650c278ee4cb5c3fa1307be9323db0d86ecee99ee96` |
| Clases JVM | 39, todas major version 52 (bytecode Java 8) |
| Miembros Android referenciados | 96 referencias únicas de constant pool; ninguna identificada posterior a API24; cero referencias de miembro sin resolver en el inventario |
| Historial API empleado | SDK37 `data/api-versions.xml`, SHA-256 `9fd47aaab29946a5f5d179797365b2d04e38132d2e7e942f5ea8504e41e6c8e5` |

La AAR está disponible localmente y coincide con el blob fijado. Su manifiesto no aporta servicios ni permisos: los gestores GlyphManager y GlyphMatrixManager hacen binding explícito al servicio **externo OEM** `com.nothing.thirdparty.GlyphService`, acción `com.nothing.thirdparty.bind_glyphservice`. La AAR no contiene ni instala ese servicio; su presencia en el teléfono no se ha comprobado. Una versión Android moderna por sí sola no implica disponer del servicio Nothing.

ApplicationLoader llama a GlyphConfig.init y a GlyphController.getInstance().init. El controlador comprueba fabricante Nothing y la preferencia OEGlyphEnabled, cuyo valor por defecto es false, antes del binding; no contiene una guarda SDK_INT explícita en init. Esas comprobaciones no prueban que la verificación/carga de todas las clases sea segura en API24. No se habilitó Glyph ni se cambió su dependencia.

La excepción de merge se limita a `com.nothing.thirdparty`, manteniendo minSdk de aplicación 24; proviene del parche ya usado por la primera unsigned. **No demuestra compatibilidad API24.** El análisis de miembros no evalúa exhaustivamente reflexión, dependencias Java/desugaring, rutas de inicialización, ART ni comportamiento OEM. El requisito declarado sigue siendo API33; no se rebaja la dependencia ni se presenta el override como una corrección de ejecución.

## Manifiesto y conservación

Se incorpora sin relajar políticas el parche realAlpha de manifiesto fusionado que ya fue necesario en la primera unsigned: excepción nominal Glyph y exclusiones explícitas de permisos/componentes SDK supervivientes al merge. Es parte de la rama de corrección; no se cambia el manifiesto Diagnostic/Beta ni el contrato histórico.

La compilación corregida debe pasar su propio manifiesto fusionado, DEX, firma ausente, JNI/Chaquopy y 96 ELF ARM64 a 4/16 KB. No se heredan esos resultados de la APK anterior. Los resultados del binario y sus hashes se entregan en el informe final separado y respaldo recuperable.

No firmar, instalar, distribuir, habilitar INTERNET/MTProto/autenticación/restauración, generar claves o usar credenciales con este PR. Los commits incluyen `[skip ci]` para omitir los eventos push/pull_request de Actions existentes, sin cambiar workflows ni lanzar workflow_dispatch.
