# Beta 44 — pantalla principal Telegram iOS

**Histórico:** este estilo y su selector se retiran en [beta 45](BETA45_DEFAULT_HOME.md).

Fecha: 11 de noviembre de 2026 (America/Bogota). Versión `1.0.0-beta.44`, build `1333`, paquete `com.flexygram.messenger`.

## Activación y migración

Ajustes de FlexyGram → Pantalla principal → Estilo de pantalla principal:

- **Por defecto** (`0`): presentación anterior y preferencias de navegación del usuario.
- **Telegram iOS** (`2`): nueva presentación Android basada en el cliente oficial de iPhone.

El retirado «Diseño esencial» (`1`) migra a `0`; no se renombra su implementación. Se eliminan su cabecera, sus accesos especiales y la proyección que ocultaba Guardados. No se eliminan chats ni carpetas del controlador. Los identificadores de antiguas carpetas favoritas pueden permanecer inertes en las preferencias; no se usan para ocultar carpetas.

El modo iPhone aplica una presentación temporal sobre la navegación: Contactos, Llamadas, Chats, Ajustes; barra flotante de 64 dp, iconos originales en espacios de hasta 28 dp y etiquetas. Las preferencias del modo por defecto no se sobrescriben. En ventanas pequeñas se conserva el desbordamiento nativo, con destinos accesibles desde Más. Si un destino no pertenece al pager activo, se abre mediante el enrutamiento existente.

## Fuente verificable

Repositorio: [TelegramMessenger/Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS/tree/24638bc69bd083981b178dd1e7f921eebbf7fc46), revisión inmutable `24638bc69bd083981b178dd1e7f921eebbf7fc46`.

| Elemento | Fuente oficial | Adaptación |
| --- | --- | --- |
| Cabecera | `ChatListHeaderComponent/Sources/ChatListNavigationBar.swift`, líneas 952–964 | 3 + 44 + 9 puntos → fila de 56 dp; Editar, título centrado y composición |
| Acciones | `ChatListUI/Sources/ChatListController.swift`, líneas 7366–7395 | Editar abre el modo de selección existente sin seleccionar un chat; composición abre contactos |
| Búsqueda | `ChatListNavigationBar.swift`, `searchScrollHeightValue()` | Recorrido de 54 dp; entrada pasiva al único editor nativo, sin consultas duplicadas |
| Avatares | `ChatListUI/Sources/Node/ChatListItem.swift`, líneas 2728–2740 | Diámetro 60 dp, borde lateral 16 dp, texto a continuación del avatar |
| Barra inferior | `TabBarComponent/Sources/TabBarComponent.swift`, líneas 870–899 | Variante de componente de 56 + 4 × 2 puntos; renderizado y selección Android existentes |
| Composición | `Images.xcassets/Chat List/ComposeIcon.imageset` | Archivo original sin redibujar, dimensiones originales conservadas por `OriginalIconDrawable` |

El nuevo icono entra en el importador reproducible de beta 41: **236 recursos originales**, 1.566 asociaciones. `tools/ios_originals/manifest.json` registra fuentes, Git blob, SHA-256 y cinco densidades. Se conservan los avisos del repositorio original. La carga de los iconos propios de este modo no modifica el paquete global elegido por el usuario.

## Integración y coste

Se reutilizan `DialogsActivity`, `DialogsAdapter`, `DialogCell`, `MainTabsActivity`, `MainTabsLayout` y la fuente compartida de blur/glass. No se añade otra lista, otro motor de búsqueda ni un controlador de cuentas paralelo. Las mini píldoras, los ajustes de avatares y los contenidos del usuario siguen perteneciendo a sus módulos existentes.

La cabecera y la búsqueda siguen los progresos nativos de scroll, selección, búsqueda y panel lateral. No crean animadores permanentes. Los materiales se retienen por vista; las capturas pertenecen al motor existente. Las operaciones de dibujo no construyen pinturas, rectángulos, imágenes ni jerarquías por frame. Sin blur disponible se usa una superficie opaca del tema. Los iconos son recursos Android cacheados; ningún importador PDF/Lottie se ejecuta en la APK.

Los controles visuales de 44 dp disponen de una delegación táctil de al menos 48 dp. La búsqueda completa es una entrada táctil de 54 dp. En transiciones, la cabecera oculta se excluye de accesibilidad. Los menús adicionales y el selector de cuenta siguen disponibles mediante pulsación prolongada en Editar/composición y toque en el título, respectivamente.

## Verificación y límites

- Suite local: **386 correctas, 39 omitidas**; las omisiones indican herramientas/corpus ausentes, no éxitos.
- Pruebas JVM de migración `1 → 0`, selección explícita de `2`, entrada segura en selección vacía, snapshot sin lecturas de preferencias durante 20.000 consultas, restauración de preferencias de navegación y orden de chats fijados con Guardados visible.
- Verificación reproducible de todas las fuentes y salidas de iconos; comprobación de sintaxis Java y recursos.
- Nuevas vistas/selector comprobados con tipos reales de Android API 35 y AndroidX Core de forma aislada; no equivale a la compilación completa. CI utiliza Android API 37 y ejecuta la suite, las comprobaciones nativas existentes y el ensamblado ARM64.

Esta es una adaptación nativa a Android, **no una copia binaria de UIKit ni una garantía de igualdad exacta de píxeles**. La tipografía sigue el sistema Android y su escala de accesibilidad. Historias, carpetas, selección y búsqueda conservan sus transiciones Android. Los estados especiales de red, insignias premium y comportamientos privados del material de Apple no se certifican como idénticos. El nombre de la opción no certifica que Apple haya distribuido una versión concreta de iOS 27. La fluidez real, la captura de blur y la respuesta del conjunto necesitan validación en dispositivos; no se han medido FPS en un teléfono durante esta revisión.

La APK oficial se genera únicamente mediante `.github/workflows/ui-beta-debug.yml`. La firma del workflow es de depuración; la clave de producción permanece bajo custodia del propietario.

## Preparación del servidor de compilación

Un intento quedó detenido por fallos DNS de `azure.archive.ubuntu.com` en la lista de mirrors de Ubuntu del runner. El flujo oficial usa ahora el archivo HTTPS oficial de Ubuntu en esa lista (incluida su suite `noble-security`), conserva las comprobaciones de firmas/TLS y limita reintentos y tiempos de descarga. La preparación tiene un máximo de diez minutos; el ensamblado nativo conserva el plazo general existente. Si falla el DNS del sistema, un helper exclusivo de CI resuelve ese único dominio mediante DNS sobre HTTPS y emite direcciones IPv4 públicas para el archivo temporal de hosts del runner. No se desactivan TLS ni firmas APT; la resolución tiene tiempos limitados y tres pruebas de regresión. Este ajuste del servidor no introduce código ni dependencias adicionales en la APK.
