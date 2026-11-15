# FlexyGram Native Test — beta.59 (1348)

Prueba solicitada para comparar el coste conjunto de las personalizaciones de
FlexyGram. Rama: `codex/flexygram-native-performance-test`.

## Identidad y respaldo

- App independiente: `com.flexygram.messenger.nativebaseline`.
- Nombre del lanzador: **FlexyGram Native Test**.
- La instalación habitual, sus sesiones y su base de datos permanecen separadas.
- Respaldo completo anterior: rama
  `backup/flexygram-before-native-test-2026-11-15` y etiqueta
  `flexygram-backup-beta58-2026-11-15`, ambas en
  `9b305e3ee7ee16097576d60af07f6ed9f105de9c`.
- Las correcciones de arranque, SQLite, reintentos, reciclaje y ciclo de vida
  realizadas hasta beta.58 se conservan. El almacenamiento de mensajes y sus
  migraciones se comparan byte a byte con ese respaldo en las pruebas.

## Qué cambia

- **Navegación inferior:** implementación de exteraLess para Telegram 13.0.2,
  con su configuración original. Se retiran el dock configurable de FlexyGram,
  sus destinos adicionales y su botón de búsqueda separado. Se mantienen la
  entrada accesible a Ajustes, el enlace de búsqueda desde Contactos y la
  comprobación de visibilidad añadida por el parche de rendimiento.
- **Música:** reproductor y minirreproductor originales de esa misma revisión
  de exteraLess. El conjunto se conserva en `app.exteraless.player.baseline`
  para evitar enlazar sus componentes con los del reproductor modificado.
  Respeta las opciones nativas de reproductor MD3/minirreproductor y su
  alternativa `AudioPlayerAlert` de Telegram.
- **Animaciones:** no se aplica el plugin ASM FastMotion. `AnimatedFloat` y
  `ActionBarLayout` usan sus duraciones originales; el inicio de la aplicación
  no carga FastMotion. Las preferencias antiguas no pueden reactivarlo por el
  cargador de configuración. Se conservan los controles nativos de Android.
- **Burbujas:** forma y superficie por defecto de Telegram, sin transparencia,
  blur de fondo, bordes personalizados, panel animado Signature ni efectos de
  borrado propios. La política de compilación ignora sus preferencias antiguas
  sin reescribirlas.
- **Reacciones:** curvas y duraciones originales en lugar del vuelo/arco
  añadido por FlexyGram. Se conservan las correcciones de propiedad, limpieza,
  espera de decodificación y avance con tiempo transcurrido.
- **Glass/blur:** política y colores de superficie de exteraLess, contorno
  original y shader de Telegram 13.0.2. Se desactivan las islas adicionales de
  glass en cabecera/entrada y el glass de selección de carpetas de FlexyGram.
  Los efectos nativos del cliente y sus controles de ahorro de energía siguen
  disponibles. Las opciones restantes de cabecera/posición del compositor se
  conservan; el compositor no utiliza su efecto de glass propio.
- **FlexyFiles/FlexyStudio:** sin accesos utilizables ni ejecución de sus
  funciones. Se retiran las asociaciones de archivos, proveedor y servicio
  Android de Studio, además de su recuperación de inicio. El reconocimiento de
  documentos y los puntos de entrada rechazan activación en este perfil.

El tipo de cuenta Android, las asociaciones de contactos y los accesos directos
apuntan también al identificador separado, evitando mezclar la integración de
cuentas con la instalación habitual.

El perfil usa `BuildConfig.NATIVE_BASELINE_TEST=true`, constante de compilación.
Los controles de funciones retiradas no reactivan trabajo oculto. Parte del
código auxiliar se conserva para mantener contratos de integración y las
pruebas de componentes; el optimizador puede eliminar rutas inalcanzables.
Los ajustes y funciones de FlexyGram ajenos al experimento se conservan.

## Procedencia de los componentes base

Código de `https://github.com/exteraless/exteraless`, revisión
`2a308f49b41534a45198c35f5ed98079f102f057` (Telegram 13.0.2).
`upstream-provenance.json` registra archivos y SHA-256 originales. No se usa la
revisión más reciente, que ya cambia contratos de Telegram a 13.2.1.
El shader de liquid glass de esta base coincide byte a byte con el que ya tenía
FlexyGram; ese archivo no necesitaba sustitución.

## Compilación y firma

El workflow existente `ui-beta-debug.yml` admite esta rama y compila ARM64 con
bibliotecas nativas optimizadas, Python y reducción de recursos. El identificador
Firebase de ensamblado también corresponde a la app separada.
Se conserva su configuración habitual `signingConfigs.debug`; no se añade un
procedimiento de creación de claves. El workflow verifica firma, ABI y registra
el certificado de la APK. Los runners anteriores no guardaban la clave debug;
reutilizar la configuración no demuestra que el certificado sea idéntico al de
otra ejecución. Esta compilación no sustituye la firma oficial de distribución.

## Validación y comparación

`tests/test_native_baseline.py` ejecuta las políticas Java reales con el perfil
nativo activado y preferencias que fallan si se consultan. Comprueba que los
ajustes retirados no se reactivan, las rutas del reproductor/navegación, la
identidad independiente, la ausencia de componentes Studio y la conservación
del almacenamiento. Se actualizan los contratos de pruebas que exigían el dock,
materiales y asociaciones de archivos retirados. Las pruebas de los componentes
conservados usan explícitamente el perfil completo en sus dobles de BuildConfig.

Para comparar en el teléfono:

1. Iniciar sesión en Native Test y dejar terminar la sincronización inicial.
2. Abrir los mismos chats y recorrer una vez sus imágenes para preparar caché.
3. Comparar reaperturas, lista de chats, conversación y navegación con la misma
   cuenta, conexión y frecuencia de pantalla. Evitar comparar una descarga
   inicial con la caché ya preparada de la otra instalación.
4. Registrar Perfetto/gfxinfo de ambas, incluyendo tiempo hasta ver filas de
   chats y tirones durante el mismo recorrido.

Aún no hay medición de rendimiento en dispositivo de esta prueba. Una diferencia
entre las dos versiones atribuiría coste al conjunto retirado; identificar una
función individual requiere reintroducir grupos por separado.

Para recuperar el código completo, usar la etiqueta de respaldo en otra rama o
volver a `codex/flexygram-beta-glass`. No requiere borrar ninguna de las apps.

## Comprobaciones locales

- Suite general tras la integración: 519 aprobadas, 43 omitidas (199,93 s).
- Pruebas posteriores del perfil, navegación e integración Studio: consultar el
  resultado del commit/workflow; incluyen las identidades de cuenta separadas.
- Tipos Java de Studio contra API37: correctos. Suite de cliente Studio: 60
  comprobaciones, con dobles explícitos de APIs Android.
- Pruebas Android aisladas de cabecera, controles de música, letras (runtime/UI)
  y efectos de borrado: correctas. Son regresiones de componentes conservados,
  no una ejecución completa de Native Test ni mediciones en dispositivo.
- Sintaxis Java, manifiesto Android, XML de cuenta/accesos directos y YAML del
  workflow verificados.

La compilación completa, firma y ABI se comprueban en el workflow asociado al
commit. Confirmar su resultado antes de considerar disponible la APK.
