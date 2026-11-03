# Editor compacto de cristal y efectos

Base: beta `1c323bf54c401204b69f1a204cb5e817d7584d17`.
Rama de desarrollo local: `feat/compact-glass-editor`.

## Interfaz

La entrada existente de efectos ahora se llama **Cristal y efectos**, en
FlexyGram → Sistema y comportamiento. No se añade otra pantalla de categorías.

La vista previa superior muestra escenas locales ficticias de Chat, Principal y
Perfil. El selector Claro / Oscuro / Tema solo cambia la vista previa, sin tocar
el tema de la aplicación. Debajo se desplazan los controles de superficie, borde
y zonas. En ventanas bajas o con fuente muy grande también se desplaza la vista
previa, para mantener accesibles todos los controles y el botón de aplicar.

- Transparencia solicitada: 0–80 %; desenfoque: 0–48.
- Preajustes: Sutil, Equilibrado e Intenso.
- Borde: estilo, grosor 0–3 dp, intensidad 0–100 %, acento o color personalizado.
- Zonas: entrada/canales, cabecera, navegación, búsqueda, carpetas, menús y perfiles.
- Restablecer modifica el borrador. Aplicar guarda y cierra; al volver con cambios
  pendientes se puede aplicar, descartar o seguir editando.

Los controles actualizan exclusivamente el borrador y la vista previa. La
configuración de materiales se escribe en una sola operación al aplicar; el
interruptor maestro conserva su mecanismo existente. La pantalla anterior se
reconstruye después del cierre, sin reconstrucciones al arrastrar cada control.
Las preferencias y las selecciones existentes se conservan al cargar.

## Renderizado y rendimiento

La configuración se lee desde una instantánea inmutable en memoria. La vista
previa no consulta cuentas, mensajes ni imágenes de red. Conserva dos bitmaps de
180 × 100 píxeles (aproximadamente 141 KiB en total), reutilizados; el desenfoque
solo se recalcula cuando cambia el radio o el fondo. Los cambios se agrupan por
fotograma y los callbacks se eliminan al separar la vista. No hay animador ni
bucle de redibujado en reposo.

El material sigue utilizando el motor nativo compartido y su captura reducida.
El radio se actualiza en las fuentes retenidas incluso si el contenido no cambió;
radio cero no construye un efecto de desenfoque. La selección de zonas determina
qué superficies reciben el material personalizado; las excluidas conservan su
presentación nativa. El radio es compartido por la fuente, **no es un radio
independiente por botón o por zona de una misma fuente**.

Los botones y acciones de perfiles y las pestañas de contenido se conectan a los
materiales y al desenfoque existentes. Los botones superiores conservan su
selector y su acción. El perfil reutiliza la captura del avatar; mantiene los
presupuestos anteriores de radio según el dispositivo (20/12/8). La ruta antigua
de desenfoque por CPU mantiene su funcionamiento anterior.

Se respetan el interruptor maestro, los ajustes de desenfoque por tema y las
restricciones de LiteMode/ahorro de energía existentes. No se introduce otro
motor, shader refractivo, captura por botón ni monitor térmico nuevo.

La transparencia efectiva puede limitarse para garantizar legibilidad: el modo
claro conserva el mínimo de alfa 184; las acciones sobre fotos de perfiles usan
ese mismo mínimo y un color de texto contrastado. Esta limitación se explica en
la pantalla. Los contornos personalizados están aislados del selector antiguo de
contornos; las superficies no personalizadas conservan su política anterior.

## Verificación sin APK

Suite completa: **249 pruebas aprobadas y 32 omitidas** (corpus externos y
artefactos generados no disponibles). Sin fallos.

Se ejecutan pruebas de la configuración real en JVM: aislamiento del borrador,
guardado y recarga, límites, caché sin lecturas repetidas, selección de zonas,
actualización del efecto retenido, radio cero, contornos y presupuesto de perfiles.
También se comprueban los recursos en español, inglés y ruso con AAPT2 y la
sintaxis de los Java modificados.

Comprobación reproducible de tipos del editor, vista previa y proveedores:

```sh
JAVA_HOME=/ruta/al/jdk ANDROID_HOME=/ruta/al/sdk \
  python3 tools/glass/check_crystal_editor.py
```

Usa la API Android 37 real y dobles pequeños de los servicios del proyecto.
No ejecuta Gradle, no empaqueta ni firma y no sustituye una compilación completa.

La validación visual y de rendimiento real sigue pendiente en dispositivo:
contraste sobre fotos, desplazamiento, perfiles propios/ajenos, cambios de tema,
RTL, ventana pequeña, fuentes grandes y modo de ahorro. No se ha compilado un APK
ni publicado esta rama durante este trabajo.
