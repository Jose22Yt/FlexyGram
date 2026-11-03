# Identidad visible de FlexyGram

Se unifica la identidad del cliente en los recursos y las rutas de salida, conservando su base técnica y compatibilidad.

## Cambios

- El nombre que usa el manifiesto (`NagramX`, un ID de recurso heredado) ahora contiene **FlexyGram**. `AppName`, `AppNameBeta`, títulos antiguos, pistas, textos de notificaciones, nombres de iconos y opciones propias se corrigieron en las traducciones incluidas. Los alias de nombre del cliente también se fijan antes de consultar cadenas remotas, para que un paquete de idioma no cambie el nombre por el de la base.
- El proyecto Gradle se llama FlexyGram. El nombre de cada APK se genera explícitamente como `FlexyGram-Beta-v…-debug….apk` o `FlexyGram-Alpha-v…-connectedAlpha….apk`, conservando los filtros de ABI/densidad si hay outputs separados. Se elimina la dependencia del nombre original del archivo Gradle.
- La carpeta predeterminada de guardado pasa a **FlexyGram**, también al actualizar una preferencia heredada cuyo valor sea exactamente exteraless. Las rutas personalizadas, incluida una ruta vacía elegida por el usuario, se respetan. Restaurar un respaldo antiguo mediante el importador Extera también normaliza ese antiguo valor predeterminado.
- Las rutas especiales de exportación a Pictures/Downloads y los directorios públicos de medios utilizan FlexyGram. Las instalaciones nuevas crean cachés con prefijo FlexyGram.
- Una caché existente puede seguir utilizando su ruta anterior para mantener válidas las referencias nativas y los archivos locales. No se mueven, borran ni renombran archivos/carpetas existentes. En almacenamiento compartido anterior a Android 11, una instalación nueva no adopta automáticamente la carpeta Telegram de otro cliente; la compatibilidad con esa ruta requiere evidencia de actualización de la instalación. Las tablas de rutas de archivos y `document.localPath` no se modifican.
- Los respaldos exportados usan el prefijo FlexyGram; conservan la extensión y el formato interoperable. También se corrigen las etiquetas de copia del informe de errores y los User-Agent propios.
- El actualizador de GitHub consulta **Jose22Yt/FlexyGram**, con una caché separada de la del proyecto base. Descarta APK con otro nombre de marca y variantes Alpha/Beta incompatibles antes de seleccionar por ABI. Esto no crea un lanzamiento ni publica una APK.
- La pantalla antigua de «Acerca de», todavía accesible desde rutas de compatibilidad, muestra la información, el código y la licencia de FlexyGram. Se conservan los créditos y el acceso al estado de centros de datos; ya no presenta canales o el repositorio de Nagram X como oficiales de este cliente.

Se conserva `com.flexygram.messenger`, las firmas, los nombres de clases/recursos/preferencias usados por plugins y enlaces antiguos, así como los créditos GPL y referencias veraces a formatos/importaciones compatibles. Los identificadores internos `app.exteraless` no son nombres visibles del producto.

## Validación

- Suite Python/JVM local con JDK 21: **244 aprobadas, 31 omitidas**.
- Pruebas nuevas: migración idempotente de la carpeta heredada; respeto de rutas personalizadas y preferencias inválidas; conservación real de un archivo en un directorio temporal; caché nueva/antigua y detección de actualización; recursos por idioma y créditos; selección real de assets por marca/variante.
- La prueba de nombre de APK ejecuta el bloque Groovy real del archivo Gradle, con outputs simulados y distintos filtros, sin configurar ni ejecutar un build Android. Se utilizó Groovy independiente para esta comprobación local; la prueba se omite si ese runtime no está disponible.
- AAPT2 compiló los 77 archivos de recursos modificados con `--legacy`. Emitió advertencias por formatos no posicionales preexistentes en traducciones, sin errores nuevos. No se generó una APK.
- El helper de identidad/compatibilidad compiló contra Android API 37. Se revisó la sintaxis Java; para el parser se normalizó únicamente en memoria un NUL ya existente en el literal XMP de MediaController. `git diff --check` correcto.

Se publica con `[skip actions]`, sin iniciar compilación de APK. Queda validar la APK futura en una actualización real: etiqueta del launcher/instalador, guardado con MediaStore, acceso a caché antigua y nombre del archivo descargado. Las carpetas ya presentes conservan sus nombres antiguos para no romper el acceso a los archivos.
