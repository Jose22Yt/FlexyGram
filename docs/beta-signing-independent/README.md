# Beta: revisión independiente antes de firma e instalación

FlexyGram1.0 — responsable @Lukhou23. Snapshot revisado de PR23:
`78151d9e8083290dca2617279cab3afb53540de6`. Rama propia; no altera cliente, JNI, Gradle, recursos,
contratos Diagnostic, main/develop ni descargas de Work2.

## Resultado independiente de Dropbox (2026-10-20)

- Carpeta /FlexyGram-Work2-Private y ZIP indicado existen. Archivo
  id:7uKZZ5yXrxEAAAAAAAAABg, revisión0165e48298ab1bd00000003314317a1.
- Tamaño observado57671850bytes; descargable según metadatos; modificación servidor
  2026-10-20T16:31:27Z. No se creó carpeta, se subió copia ni se cambiaron permisos.
- Las listas directas de enlaces de carpeta y ZIP devuelven0, has_more=false/cursor vacío.
  Esto acredita esas consultas completas del usuario conectado; NO enumera todos los
  miembros, invitaciones ni enlaces emitidos por otros usuarios.
- Cuenta conectada personal. El identificador de namespace raíz coincide con el parent
  reportado; ese campo por sí solo no demuestra que una carpeta esté compartida o privada.
  permissions={} no equivale a can_read/can_write=true ni a «sólo propietario».
- La herramienta no expone listado de miembros/invitaciones. El responsable debe revisar
  «Administrar acceso» de ESTA carpeta y confirmar que no hay personas/grupos/invitaciones
  no aprobados antes de guardar una APK real. No se modifica acceso desde esta auditoría.
- Se emitió un enlace temporal de un uso/60s como comprobación del endpoint de descarga.
  No se consumió ni publicó. No es un enlace compartido persistente y no se guarda aquí.
- SHA256 esperado según el recibo publicado de Work2:
  2094cb8985a1cf26d909f83272d20a977c1c541706ce218b3104cbecd8769c6d.
  content_hash reportado por Dropbox:
  4761b071f7a5edee928d7553ec8f464c010133b1a6758c845a0d7c86d03c5f62.
  Son algoritmos/valores distintos: NO compararlos como SHA256 del mismo archivo.
- Esta sesión sigue sin entorno de ejecución: «No usable execution environment is available».
  NO se descargaron bytes, calcularon SHA256/CRC ni reprodujo la recuperación de Work2.
  El recibo publicado en78151d9e todavía describe el intento anterior403; la existencia
  actual del ZIP es evidencia nueva de metadatos, no una actualización inventada del recibo.

Para completar independencia, en un contexto ejecutable distinto del de subida:
pedir un enlace NUEVO del file_id/revisión anterior, descargar una sola vez sin HEAD/Range,
comprobar tamaño/SHA256 y zipfile.testzip(), y registrar revisión/fecha/resultado.
Si cambió revisión o hash, detenerse. No exigir volver a subir el mismo ZIP.
Una lectura de metadatos o emitir URL no constituye recuperación de bytes.

## Identidad y custodia beta (sin generar clave)

Nombre de propósito: FlexyGram Beta personal offline, separado de Diagnostic/Production
y de Exteraless. El nombre/alias de clave no prueba identidad: fijar huella SHA256 del
certificado DER revisado antes de firmar. Una clave dedicada, un firmante esperado,
sin rotación/linajes improvisados en esta primera prueba.

Antes de generar: acordar quién custodia, ubicación privada y una segunda copia
recuperable cifrada, control de acceso y procedimiento de recuperación. Contraseña
fuera del repositorio/logs/chat y separada del material cifrado. Dropbox para APK no
implica automáticamente autorización para guardar allí una clave. No publicar certificados
o claves en GitHub; el expediente sólo necesita huella pública y referencia de aprobación.

La prueba de recuperación de custodia debe demostrar que el entorno autorizado puede
abrir la copia y obtener el certificado/huella esperados. No autoriza firmar una APK
cualquiera. Hace falta aprobación separada del unsigned concreto por hash/commit/versión.

`checklist.draft.json` es una lista de requisitos/estado, NO un recibo de autorización.
Sus valores false/null son deliberados. No convertirlos en true por pasar pruebas sintéticas.

## Integración de verificadores existentes, sin repinar Diagnostic

1. Work2 entrega APK unsigned nueva, hash y versión, commit exacto, clases Java del mismo
   build, manifiesto/DEX/ELF/grafo y recibo privado de recuperación. Reusar
   tools/beta_handoff/gate.py sobre sus bytes. No usar la APK98de… para el código actual.
2. El gate unsigned rechaza firmas por diseño: ejecutarlo ANTES de firma. Los controles
   javap sobre clases externas no equivalen a leer todos los campos DEX del APK.
3. tests/native_compatibility/verify_post_sign_diagnostic.py tiene primitivas reutilizables:
   members, check_signature, check_alignment y strict_json.
   NO invocar su verify completo/approved_identity con beta: fija el APK/contrato histórico
   Diagnostic y scope Diagnostic_lab_only. No pasar un recibo beta como si fuera Diagnostic.
4. Preparar/adaptar un wrapper beta leído/revisado independientemente que:
   - valide autorización beta por hash unsigned, commit, huella, recuperación y referencia;
   - recompruebe hash real unsigned y aceptación PR25;
   - compare members(unsigned)==members(signed) para todo payload no de firma;
   - exija hash firmado distinto, exactamente un firmante y huella aprobada, v2 válido
     mediante check_signature; sin aceptar stdout de una ejecución fallida;
   - ejecute check_alignment sobre el FIRMADO y vuelva a inspeccionar identidad/manifest;
   - escriba informe nuevo exclusivo privado con ambos hashes/huella/comandos/resultados.
   Falta implementar/ejecutar ese wrapper y sus regresiones con Python/SDK disponibles.
   Esta sesión no añade código Python sin ejecutar ni afirma tener ese gate binario listo.

La igualdad de inventario y bytes descomprimidos debe incluir AndroidManifest.xml,
todos los DEX, recursos y assets Chaquopy, .so de JNI/Python y metadatos funcionales.
No excluir META-INF entero: como máximo las entradas de firma concretas que el verificador
revisado reconoce. Rechazar otros cambios, entradas duplicadas/CRC erróneo o nuevas rutas.
La firma cambia el hash del contenedor; no se espera igualdad de hash de ambas APK.
El bloque v2 no es una entrada ZIP; no confundirlo con una alteración permitida del DEX.

Una adaptación debe probar: falta de autorización/huella/custodia; scope Diagnostic usado
por error; certificado incorrecto/varios firmantes; verify exit!=0; v2 inválido;
cambio de INTERNET/components/DEX/so/assets; contenido añadido/borrado; corrupción ZIP;
zipalign fallido; hashes diferentes a los recibos; copia recuperada distinta.
No repetir367/85/21 ni atribuir pruebas anteriores a este wrapper inexistente.
No preparar comandos de firma con contraseñas en argv ni habilitar firma automática.

Comprobaciones futuras de sólo lectura:
`apksigner verify --verbose --print-certs --min-sdk-version 24 APK_FIRMADA`
y `zipalign -c -P 16 -v 4 APK_FIRMADA`.
No se ejecutaron aquí. El SDK del operador debe soportar el rango que se pretende verificar;
un resultado estático no garantiza aceptación en HyperOS/Android17, coexistencia,
instalación efectiva, arranque o carga JNI/Python. Sólo el dispositivo lo puede confirmar.

## Hallazgos nuevos sobre primer arranque / navegación

### BETA-BACK-36 — alta, incompatibilidad estática frente al contrato documentado

- build.gradle:46–48 fija min24/target36.
- src/betaDevelopment/AndroidManifest.xml:139 enableOnBackInvokedCallback=true;
  Activity:146–147 no lo sobrescribe.
- BetaPreviewActivity.java:27 extiende android.app.Activity;135–139 sólo override legacy
  onBackPressed y requestClose. No registra OnBackInvokedCallback ni dispatcher AndroidX.
- Android documenta que, target36 y Android16+, no se llama onBackPressed ni se despacha
  KEYCODE_BACK con la ruta predictiva habilitada.

Consecuencia que debe comprobarse: Back del sistema puede terminar Activity en lugar de
pasar por la cola BACK; la flecha interna sí llama requestClose. No se declara reproducción
en Android ni crash confirmado. Reproducción futura: abrir Conversation sintética,
comparar flecha y Back/gesto en API36+/37; repetir durante transición y revisar chat_close.

Propuesta limitada para Work2: en esta Activity beta, registrar OnBackInvokedCallback
API33+ que delegue exactamente a requestClose cuando requests exista, o cierre la
Activity fallida si no existe; conservar onBackPressed como ruta API24–32. Desregistrar
el callback al destruir. Cubrir SDK<33, callback tras init fallido, pausa/recreación y
Back durante transición con el mismo mecanismo de cola. No cambiar el manifest global,
animaciones ni navigation engine para ocultar el hallazgo. Propuesta, NO parche aplicado.

### BETA-POSTINIT-REENTRY — alta, ruta de fallo condicional por inspección

ApplicationLoader.java:230–235 devuelve si applicationInited=true y lo fija antes de
terminar;286–341 hay inicializaciones posteriores. BetaPreviewActivity.java:53–61
captura fallo y muestra POST_INIT_FAILED, pero no conserva un latch de fallo por proceso.
Si escapa una RuntimeException/LinkageError DESPUÉS de fijar el flag, recrear Activity
en el mismo proceso hace que postInitApplication vuelva normalmente por el early return,
sin probar que finalizó. Se puede intentar construir UI sobre inicialización parcial.

Contraejemplo/reproducción host pendiente: primera llamada real instrumentada fija flag
y lanza fallo controlado; primera Activity muestra bloqueo; recrear segunda en mismo
proceso; verificar que NO cree ActionBarLayout. Las pruebas de un fallo aislado no cubren
automáticamente este segundo intento. No se ejecutó ese arnés aquí y no se afirma crash real.
Propuesta: estado/latch de fallo sólo beta y a nivel de proceso, no restaurado como éxito
desde Bundle; un fallo terminal sigue bloqueando la UI hasta proceso nuevo. NO resetear
a ciegas applicationInited ni repetir inicializaciones globales parcialmente completadas.

### Antes de Activity — pendiente Android, no defecto nuevo demostrado

ApplicationLoader.onCreate:398–403 ya carga JNI y puede lanzar por UnsatisfiedLinkError,
antes de la pantalla POST_INIT_FAILED. La pantalla de diagnóstico no cubre ART/Application.
LocalPythonProbe distingue carga/start/import, pero no puede certificar JNI que impidió
crear la Activity. Conservar captura acotada de primer arranque/PID y fallo de proceso.
BetaUiState conserva sólo3 primitivos, no credenciales ni un «Python listo» restaurado;
el productor marca abandonos/pérdidas y el importador rechaza lotes incompletos. No se
demostró un defecto nuevo en esas rutas por esta lectura.

## Antes de entregar para instalar

Requerir: privacidad de carpeta aprobada; APK nueva recuperada; gate unsigned;
custodia recuperada/aprobada; autorización de firma del hash concreto; comparación
postfirma/certificado/alineación; hash firmado conservado y recuperado; aprobación
independiente de entrega privada, instalación y prueba offline en teléfono identificado.
Mantener API0/hash vacío/seis false/sin INTERNET y sandbox propio. Sin cuentas reales,
sesiones heredadas ni servicios remotos. Si una puerta falla, no etiquetar instalable.

Resultados de ESTA sesión: metadatos y enlaces consultados; snapshot fuente revisado;
archivo JSON validado sintácticamente.0 pruebas Python/SDK/Android y0 bytes ZIP verificados.
No se generaron claves, firmó, instaló, distribuyó o recompiló APK; ningún permiso cambiado.

Fuentes:
- https://developer.android.com/about/versions/16/behavior-changes-16#predictive-back
- https://developer.android.com/tools/apksigner
- https://source.android.com/docs/security/features/apksigning/v2
