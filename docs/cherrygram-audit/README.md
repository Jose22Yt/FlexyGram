# Auditoría y corrección de la adaptación Cherrygram

## Procedencia y límite de la evidencia

Fuente Beta auditada: `bf96667efac14d0cbbf6677471890a366c3ef3c0`, HEAD de `feat/beta-official-source-v2`, que incorpora el PR #167. El workflow `beta-private.yml` en `main` (`49ccce7492b58f1d402380cc71d93391d905c205` al revisar) fija exactamente ese SHA para código de aplicación. El PR #169 cambia el pin de entrega; su HEAD de infraestructura no es el commit del cliente.

**Commit de la APK instalada: NO DETERMINADO.** El dossier tampoco lo demuestra. No se recibió la APK, su SHA-256 vinculado al informe de entrega ni acceso ADB al Poco. Las capturas no se atribuyen automáticamente a la fuente Beta actual. Para cerrar esta condición hace falta el identificador de compilación mostrado por la aplicación o el hash de la APK instalada contrastado con los metadatos de su compilación. Un número de versión por sí solo no basta. Las correcciones siguientes se basan en defectos reproducibles en código/geometría, no en una supuesta reproducción física de esas capturas.

La copia privada del dossier se mantiene fuera del repositorio. Ninguna de sus cinco imágenes, contactos o contenidos se incluye en este PR, sus artefactos o nuevas pruebas.

Referencia pública inspeccionada: [Cherrygram, commit 3050af6d948acc27db446f6cd27a8e200b205c1b](https://github.com/arsLan4k1390/Cherrygram/tree/3050af6d948acc27db446f6cd27a8e200b205c1b), en particular `ChatsPreferencesEntry.java`, `MainTabsActivity.java` y blur3. Su dock utiliza fuentes RenderNode de fragmentos y una búsqueda fuera de la lista de pestañas. La licencia raíz es GPL versión 2. Aquí se adapta el comportamiento de forma independiente sobre los componentes ya presentes en FlexyGram; no se importan clases ni bloques no triviales de Cherrygram ni se presume paridad con versiones no publicadas. Se conservan los avisos existentes.

## Hallazgos y correcciones

| Incidencia | Causa y evidencia de código | Corrección implementada | Estado de validación |
|---|---|---|---|
| Contador sobre Glass | `SignatureChatHeader.draw()` retornaba antes de `drawUnread()` | Dibuja el contador después de la superficie nativa; restaura el color prestado de TextPaint | Flujo comprobado por prueba de fuente; prueba Canvas preparada, ejecución Android pendiente |
| Contador en Fusion/Portrait | `measure()` anulaba ambas banderas de contador sin reservar anchura | Reserva anchura en la geometría retenida; cuenta integrada o cápsula separada según la preferencia existente; respeta RTL y objetivos táctiles | 1.920 combinaciones de geometría Java ejecutadas; comportamiento físico pendiente |
| Contador separado con Glass | La ruta nativa dibujaba el rectángulo conjunto, no la cápsula independiente | Drawable retenido propio para la cápsula, misma fuente blur3; no reutiliza el RenderNode de otra isla | Fuente y geometría comprobadas; renderizado integrado pendiente |
| Borde duplicado Fusion | `drawForeground()` pintaba un borde adicional encima del que acababa de dibujar Glass, incluso al ocultarlo | El primer plano Matte no añade ese segundo borde cuando se dibujó Glass | Comprobación de fuente; comparación de ambos temas en Android pendiente |
| Activación Liquid Glass en caliente | Fuente final nula si el chat se construyó con el efecto apagado; el supresor nativo también fija la política en su constructor | Prepara fuente nativa dentro del gate existente de capacidad/blur; reconstruye el supresor y reconecta las fuentes únicamente al cambiar política | Lógica comprobada; necesita prueba de RenderThread en dispositivo |
| Notificación de política | `LiteMode.setAllFlags()` guardaba sin avisar a las superficies retenidas | Notifica cambios reales; recorre una instantánea para permitir que una vista se desregistre durante el callback | Métodos reales extraídos ejecutados con host UI declarado como doble; no equivale a ejecutar Telegram |
| Dock opaco | Fuente anulada y fondo GradientDrawable sólido | RenderNode blur3 con RenderEffect nativo, fuente recortada a la franja del wrapper; sólo captura ViewPager, nunca dock/player/overlay | Integración de código y pruebas de fuente; GPU/framestats/captura real pendientes |
| Fuente del dock desactualizada | Una fuente debe cambiar al hacerlo el contenido inferior, no por sondeo | Revisión de contenido desde `onDescendantInvalidated`, dimensiones/posición en hash e invalidación de drawables; no bucle en reposo ni bitmap de pantalla | Comprobación de fuente; medir frecuencia de grabación y coste GPU en Poco |
| Buscar sólo como pestaña | El controlador sólo creaba destinos dentro de MainTabsLayout | Opción «Burbuja de búsqueda separada»; botón circular hermano del dock, espacio reservado, RTL, descripción accesible, búsqueda real de chats y exclusión de SEARCH del dock | Comprobaciones de rutas y recursos; interacción integrada pendiente |
| Selector de iconos sin toque | La propia fila es un RecyclerListView; su adaptador devolvía deshabilitado. RecyclerListView aplica `child.setEnabled(false)` y su interceptor rechaza eventos | Mantiene habilitado el selector; errores del PackageManager no cambian la selección visual ni generan confirmación de éxito | Flujo comprobado; aliases del manifiesto fuente verificados; HyperOS/manifest fusionado pendientes |
| Tintes tras cambiar tema | El dock sólo limpiaba fragmentos ocultos; `FilterTabsView.updateColors()` no renovaba los drawables de selección | Actualización de dock, colores cacheados y búsqueda tras el callback de tema; renovación de ambos selectores de carpetas con sus tokens existentes | Fuente/recursos comprobados; no se afirma resuelta toda variación de un tema personalizado sin ejecutarlo |
| Recorte del mensaje seleccionado | La previsualización se traslada/escala pero seguía recortada al rectángulo de su fila original | Omite ese recorte de origen sólo para la previsualización transformada; mantiene límites de contenedor, viewport, insets y animaciones | Error de coordenadas reproducido por caso sintético. Correspondencia con la captura pinned y resultado físico pendientes |
| Contraste de contorno sólido | Un divisor casi transparente puede ocultar el borde en la fuente temática | El proveedor Themed resuelve un contorno de texto temático con alpha acotado, según claro/oscuro | Revisión de fórmula; capturas y contraste físico pendientes |

No se duplica `GlareMode`, `GlareSettingsSection` ni `StaticOutlineStroke`: se conservan exactamente los del PR #165/#167, incluyendo `OEAppearanceGlassOutlineStyle`, sus valores y el camino predeterminado. Glare controla contornos; no enciende blur. Los fallback Matte siguen siendo fallback, no se presentan como Liquid Glass.

## Límites y riesgos concretos

- Si el chat se creó con **el blur general de chats desactivado**, la arquitectura original no tiene fuente nativa. Conserva el fallback: puede requerirse reabrir ese chat al habilitar el blur general. La corrección en caliente cubre Liquid Glass cuando ya existe la infraestructura blur. No se promete una recreación imposible de campos/fuentes inexistentes.
- La nueva fuente del dock funciona en hardware Android 12+ y respeta blur general y Liquid Glass. En software, API anterior o ahorro incompatible se dibuja la superficie sólida original. El registro se limita a la altura del wrapper; no hay capturas de bitmap ni trabajadores permanentes. Debe medirse su coste real, especialmente durante scroll y música.
- Renovar el supresor al cambiar política puede liberar recursos GPU posteriormente por GC; verificar presión de memoria tras alternar repetidamente. No ocurre por fotograma.
- La búsqueda separada es opcional y está apagada por defecto. No elimina SEARCH del orden guardado: lo filtra únicamente del dock visible. La ocultación superior sólo restaura elementos que esta función haya ocultado; no fuerza a aparecer un buscador que Telegram ya ocultaba. Mantiene el campo activo y el botón Atrás originales.
- Los alias y la persistencia `flexy_launcher/selected` no cambian. Android/HyperOS puede actualizar su caché visual después del cambio efectivo de PackageManager. No se puede certificar ese comportamiento sin el dispositivo y el manifiesto final fusionado.
- El cambio de clipping es específico del overlay seleccionado, no una desactivación global de clipping o blur. Ensayar grupos de medios, mensajes largos, tareas, reacciones personalizadas, teclado y panel fijado/traductor.

## Validación

Ver `results.json` para resultados exactos. Comandos desde la raíz:

```sh
python3 -m pytest -q tests
PYTHONPATH=tools/connected_alpha python3 -m unittest tools.connected_alpha.test_header_fusion tools.connected_alpha.test_header_portrait tools.connected_alpha.test_context_panel tools.connected_alpha.test_signature_launcher1275 -v
python3 tools/settings2/checks.py
PYTHONPATH=tools/connected_alpha python3 -m unittest tools.connected_alpha.test_header1273 -v
./gradlew --version
```

Se amplían los probes existentes `header_visual` y `liquid_navigation`; se declaran sus dobles y NO se presentan como compilación del cliente ni GPU real. La prueba Canvas nueva del contador debe ejecutarse con SDK/Maven junto a los probes ya existentes:

```sh
python3 tools/connected_alpha/header_visual/run.py --sdk-root "$ANDROID_HOME"
python3 tools/connected_alpha/liquid_navigation/run.py --sdk-root "$ANDROID_HOME"
python3 tools/glare/android/run.py --sdk-root "$ANDROID_HOME"
```

El entorno tiene Java 17, sin SDK Android/JDK21/Maven preparados. El wrapper falla descargando Gradle 9.7.1 (`Network is unreachable`). No se completó compilación Android ni ejecución Canvas en esta auditoría. La sintaxis Java21 se comprueba separadamente con JavaParser; no es compilación semántica. No se genera APK ni se cambia workflow, pin de producción, firma, versión, paquete, secretos, autenticación o sesiones.

Los gates históricos siguen activos: `settings2/checks.py` detecta correctamente que ChatActivity/LiteMode salen del alcance del viejo rediseño de ajustes. La nueva misión los requiere explícitamente, pero esa ampliación necesita revisión de integración: no se borra ni se relaja el gate. `test_header1273` falla también sobre la base intacta (dos fallos y un error); sus controles antiguos de hash/API/locales no son evidencia de regresión nueva. No se declara CI completamente verde.

## Aceptación física y capturas requeridas

No hay capturas nuevas del cliente ejecutándose ni mediciones FPS/latencia/memoria: **pendientes**. Las fotos privadas no sustituyen evidencia antes/después sobre el mismo commit.

1. Identificar APK baseline: commit de información/compilación o SHA-256 contra su informe de entrega. Mantener cuenta y sesión; no desinstalar ni borrar datos.
2. Compilar el candidato mediante el procedimiento Beta protegido vigente, después de revisar el nuevo SHA. No cambiar aquí los pines de distribución ni ejecutar material de firma sobre código sin aprobar.
3. Cabecera Classic/Signature/Fusion/Portrait: 0/9/10/99/100 no leídos; contador integrado/separado, RTL, fuentes grandes, dos temas y tema personalizado. Verificar cápsulas, hit targets, título, llamadas, ningún doble borde.
4. Alternar Liquid Glass y ahorro de energía con chat abierto y después de volver de ajustes; fallback software/blur apagado; ausencia de franjas sólidas cuando la fuente es compatible.
5. Dock con contenido de prueba desplazándose detrás: distinguir desenfoque real de alpha; 3–6 pestañas, con/sin burbuja, RTL, teclado, música, cambios de orientación e insets. Tocar Buscar una vez, volver, alternar opción y comprobar una sola ruta visible.
6. Seleccionar tres iconos, cerrar/reabrir, reiniciar teléfono y actualizar sin borrar datos. Comprobar PackageManager y selección recordada, además de la caché visual de HyperOS.
7. Cambiar temas con Home abierto: filtros, texto/badges/avatares, títulos de grupos/bots/canales/contactos y búsqueda. Capturar sólo una cuenta de pruebas sin conversaciones privadas.
8. Menú con fijado/traductor: mensaje alto, álbum, teclado y scroll; abrir/cerrar, desplazar la previsualización y ejecutar acciones. Comprobar el borde superior en transición y al quedar estable.
9. Utilizar `tools/connected_alpha/performance/` con frecuencia efectiva, misma carga/caché/temperatura y varias repeticiones. Comparar framestats/Perfetto y memoria; revisar que no haya grabaciones RenderNode en reposo. No atribuir duración de fotograma a latencia táctil.

Integración: rama independiente desde `bf96667`; PR contra `feat/beta-official-source-v2`. No se fusiona main ni se modifica el pin de entrega. Revisar cada bloque, ejecutar compilación y pruebas Android, aceptar físicamente y sólo después preparar el siguiente pin Beta mediante el procedimiento autorizado. Revertir el commit restaura el comportamiento anterior; no se migran preferencias y la clave opcional `separate_search` queda inerte.
