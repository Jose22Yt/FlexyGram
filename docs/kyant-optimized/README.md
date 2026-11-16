> Registro histórico de beta63. La implementación actual de beta64 se describe en [Interacción elástica](../elastic/README.md).

# Kyant en la base principal optimizada

Base: `d50640dec57ee26c957b2b0342fe47cf4006acf5` (Native Test beta60).
Rama: `codex/flexygram-optimized-kyant`. Paquete conservado:
`com.flexygram.messenger.nativebaseline`; beta63/code1352.
La etiqueta `flexygram-optimized-base-beta60` conserva la base previa.
El experimento antiguo Glass Lab se mantiene separado.

## Un solo motor óptico

Se eliminan `LiquidGlassEffect.java` y `liquid_glass_shader.agsl` de Telegram.
Ninguna ruta de producción puede instanciar ese motor ni cargar su programa.
La captura compartida y el blur normal de View/RenderNode se conservan: son
infraestructura de escena, no un segundo motor de refracción.

La barra principal usa el componente original `LiquidBottomTabs` de Kyant Backdrop
2.0.1 y sus seis archivos originales con procedencia SHA256 y licencia Apache2.
Mantiene controles/iconos/badges/callbacks nativos, long press y accesibilidad.
Mientras Kyant dibuja, `MainTabsLayout.draw()` no pinta el fondo ni el selector
anterior; los selectores interiores de los iconos también se suprimen.

Las demás superficies mantienen sus vistas, foco, teclado, accesibilidad y geometría.
`KyantGlassEffect` adapta directamente `RoundedRectRefractionShaderString` del mismo
repositorio a RuntimeShader. El AGSL es idéntico, expandiendo únicamente la
interpolación Kotlin de RoundedRectSDF. Su huella queda en
`third_party/kyant-backdrop/native-shader-provenance.json`.
Las fuentes compartidas suministran blur8dp/vibrancy1.5 una sola vez, y cada panel
aplica la lente24dp limitada al semitamaño mínimo para evitar gradientes indefinidos
en controles pequeños. Es la misma óptica con una integración View; no se afirma
identidad píxel a píxel con un catálogo Compose de geometría diferente.

## Ámbito explícito

`create()` crea fondos normales, incluso si la preferencia Kyant está habilitada.
Únicamente `createKyant()` permite refracción, y el drawable conserva ese permiso
independientemente de los cambios generales de energía/tema.

Superficies autorizadas:

- Barra inferior principal (componente Compose original).
- Fila de carpetas y filtros de chats: un panel compartido, sin capas por celda.
- Cabecera de conversaciones: avatar, volver, menú y panel superior.
- Compositor y controles inferiores de conversación, incluidas acciones de canales
  y los controles de grabación; el panel bajo el teclado sigue sin refracción.
- Pestañas del perfil (historias, regalos, archivos, etc.).
- Campo y filtros de búsqueda, incluidos los filtros de búsqueda en conversación.

Los menús contextuales, reproductor, adjuntos, emojis, otras cabeceras y demás
pantallas no reciben refracción por usar una fábrica compartida.
Se conserva la desactivación de FlexyFiles, FlexyStudio, navegación personalizable,
efectos de burbujas y FastMotion; no se toca el almacenamiento ni la carga de chats.

## Trabajo y compatibilidad

No hay capturas Bitmap/PixelCopy ni lecturas GPU→CPU. Dock recortado con margen
óptico y revisión por invalidación; no hay ticker en reposo ni recomposición de
controles por un simple scroll. Los paneles nativos reutilizan el programa de texto,
un shader mutable propio y efectos mientras no cambie su geometría. Los shaders
no se construyen para superficies ocultas durante createView.

La composición, callbacks, listener de energía y captura del dock se liberan al
separarse de la ventana. La preferencia de ahorro conserva su bit para migración,
renombrado FLAG_KYANT_GLASS. El interruptor existente es la única autorización
para la refracción: no hay activación automática. Se retira la migración de beta62;
si existe su marcador `kyant_material_v1`, se apaga su activación forzada una sola vez
y se elimina el marcador. Los siguientes encendidos/apagados explícitos se conservan,
incluido al reiniciar, sin modificar el resto de preferencias. Ahorro de energía, hardware
no disponible y versiones anteriores conservan fondos normales, nunca el motor viejo.

## Validación reproducible

- `pytest tests/`: comportamiento del cliente, ausencia del motor retirado,
  superficies explícitas, procedencia y presupuestos de trabajo/cachés.
- `python tools/kyant_lab/android/run.py --sdk-root "$ANDROID_HOME" --output-dir /tmp/kyant-check`:
  compilación del puente real con Compose/Skia; dobles explícitos solo para APIs
  anfitrionas. Distribución física LTR/RTL/redimensionado y compilación real del AGSL.
  La prueba de contenedor reproduce con Compose real que el MATCH_PARENT anterior
  expande el WRAP_CONTENT a toda la pantalla e intercepta los controles nativos.
  KyantDockContainer obtiene su altura de la barra nativa, márgenes e insets antes
  de medir el overlay. Se comprueban clicks sobre cabecera/lista/conversación,
  paso de gestos de scroll y barra oculta. Los controles son fixtures explícitos;
  no se afirma una prueba de navegación completa en el dispositivo del usuario.
- Workflow ARM64: compila Java/Kotlin antes de ensamblar JNI/Python, valida firma/ABI.

Estas pruebas no miden FPS, consumo GPU ni apariencia en un teléfono. La prueba
satisfactoria del usuario en Glass Lab valida su dock anterior, no todos los nuevos
paneles ni el coste de esta integración. No se prometen cero tirones sin Perfetto
comparativo sobre esta compilación en el mismo dispositivo y estado de caché.
