# FlexyGram — Auditoría de navegación y fluidez N1

**Estado:** primer inventario de código, independiente de P0.4c. **No se ha medido FPS ni latencia en Android.** Autor del proyecto FlexyGram: @Lukhou23. Rama auxiliar nacida de \`develop\` en \`ab063041804674861e865364206c0ef27ef1e953\`.

Este PR **no cambia** animaciones, duración de transiciones, políticas, JNI, Python, build, credenciales, autenticación, manifest ni código funcional. Conserva GPL, créditos y nombres técnicos heredados.

## Evidencias verificadas directamente sobre el código

El archivo central es \`TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java\` (blob \`bccb9dc2ea996f6add397fcf076a7fb8a83aca07\`).

| Hallazgo | Fuente aproximada | Observación comprobada |
| --- | --- | --- |
| Apertura | ActionBarLayout.java:2446 | \`presentFragment(NavigationParams)\` devuelve \`false\` si \`checkTransitionAnimation()\`, \`animationInProgress\` o \`startedTracking\` bloquean la ruta |
| Cierre | ActionBarLayout.java:3106 | \`closeLastFragment(...)\` retorna sin cerrar cuando hay transición/gesto activo |
| Retroceso | ActionBarLayout.java:2030 | \`onBackPressed()\` retorna durante transición/gesto |
| Recuperación | ActionBarLayout.java:2130 | \`checkTransitionAnimation()\` provoca limpieza si han pasado 1500 ms desde el inicio de una transición, o por preview. **No equivale a un temporizador autónomo:** requiere que se invoque el chequeo |
| Preview | ActionBarLayout.java:2127 | \`checkTransitionAnimation()\` retorna \`false\` si \`transitionAnimationPreviewMode\`; hay que probar este camino aparte |
| Teclado y apertura | ActionBarLayout.java:2780 | Una ruta condicionada por teclado espera **250 ms** antes de iniciar la transición |
| Apertura diferida | ActionBarLayout.java:2759 y 2793 | Una ruta condicionada por \`needDelayOpenAnimation()\` programa **200 ms** (no todas las aperturas) |
| Teclado y cierre | ActionBarLayout.java:3237 | Una ruta condicionada por teclado programa **200 ms** |
| Limpieza | ActionBarLayout.java:2055–2100 | \`onAnimationEndCheck(byCheck)\` ejecuta callbacks, cancela animación por chequeo, limpia tareas/escala/traslación; no es seguro sustituirla por cancelación arbitraria sin pruebas |
| Delegación | BaseFragment.java:488–496 | \`finishFragment(boolean)\` devuelve \`true\` después de llamar a \`closeLastFragment(animated)\` (que devuelve \`void\`), aunque ésta puede no continuar bajo las guardas |
| Deslizamiento de la lista | DialogsActivity.java:1404 | El movimiento horizontal de lista consulta \`!parentLayout.checkTransitionAnimation()\` |

Los mecanismos encontrados **son coherentes con la sensación de toques ignorados durante una transición**, pero no prueban por sí mismos un problema en el dispositivo ni permiten afirmar cuánto retraso percibe el usuario. Algunos bloqueos son intencionales y necesarios para evitar inconsistencias en el stack.

## Herramienta incluida

\`tools/navigation_performance/audit.py\` es Python estándar, de solo lectura. Produce JSON con el ID del hallazgo, fichero, línea, tipo (gate/conditional_wait/fallback/exception/cleanup/semantics) y retardo literal cuando existe. La opción \`--strict\` falla si no encuentra las 11 señales esperadas; **no falla por la existencia de esperas válidas**.

\`tests/navigation_performance/test_audit.py\` contiene **13 pruebas sintéticas** independientes de Android, con casos mutados para detectar la eliminación/cambio de condiciones, retardo modificado, ruta preview, cierre/base fragment y falsos positivos por tokens fuera del método. No usa red ni cuenta Telegram.

~~~bash
python -m unittest discover -s tests/navigation_performance -v
python tools/navigation_performance/audit.py --strict
~~~

Inspección directa del código mediante GitHub: **11 de las 11 señales detectadas** en el SHA base. **No se ha ejecutado todavía la suite Python contra el checkout completo del proyecto en este turno**: Work debe ejecutarla y guardar salida JSON. Estas señales son fuentes y líneas, no resultados de instrumentación ni una regresión de FPS.

## Experimento Android posterior (solo con autorización y entorno aislado)

1. En una variante de laboratorio **sin autenticación, datos ni servicios remotos**, añadir trazas opcionales en puntos del ciclo de vida: touch recibido; solicitud de \`presentFragment\`/\`closeLastFragment\`; aceptación/rechazo y motivo; \`onTransitionAnimationStart\`; \`onTransitionAnimationEnd\`; primer frame visible.
2. Con reloj monotónico, Perfetto / FrameTimeline / Android JankStats según compatibilidad, capturar latencia toque→aceptación, toque→primer frame, frames perdidos y percentiles p50/p95; reportar ABI/API, escala Android y estado de teclado.
3. Casos reproducibles: 1 toque, 3–5 toques rápidos, retroceso inmediato, vista previa/peek, teclado abierto, finalización de animación, tema oscuro, arranque en frío y caliente. Usar únicamente fixtures y entorno autorizado.
4. Contrastarlos con una **base Exteraless del mismo entorno** cuando legal y técnicamente disponible, sin copiar ciegamente un motor de navegación ni alterar la identidad.
5. Probar invariantes antes de tocar la lógica: tamaño/orden del stack, exactamente una transición activa, callbacks de inicio/fin completos, ningún fragmento destruido dos veces, sin congelación de preview, sin errores en Android/API24–37.
6. Sólo si los datos confirman cuello de botella, proponer un PR funcional separado con pruebas que preserven integridad de la navegación. No recortar el watchdog ni transformar los \`return\` en cancelaciones indiscriminadas.

## Integración y restricciones

- Revisar el PR antes de fusionarlo. Ningún merge a \`main\`, \`develop\` u otra rama realizado aquí.
- Work continúa P0.4c de Android/16 KB en sus propias ramas; este PR no cambia sus archivos.
- No activar Actions, cuentas, red, permisos, FCM, push, traducción, plugins ni producción.
- No declarar que se corrigió lag, que se probó instalación/ART ni que hay APK nueva.
