# realAlpha corregida — prueba manual exclusivamente en teléfono

Estado: procedimiento preparado, **sin firma, entrega al teléfono, instalación ni ejecución autorizadas**. El usuario indica Android 17 en su teléfono principal; registrar después la versión y compilación que muestre Ajustes. Este procedimiento usa únicamente el teléfono durante la prueba y no exige PC, ADB, root, cuenta Telegram ni servicios de laboratorio.

## Identificación y autorización previa

La APK anterior `b5f072c882a71d62c915f9a6a2fade3fbdcfc23ec4ae5b44e1d63e292d12ead2` no contiene la corrección de Atrás y no sirve para aceptar este cambio.

Antes de cualquier firma: presentar el SHA-256 de la nueva unsigned, el commit y la huella SHA-256 del certificado concreto propuesto. El usuario debe autorizar expresamente esa combinación; no generar ni sustituir identidades. Tras firmar una copia, registrar su nuevo tamaño/SHA y la relación de contenido con el unsigned conservado. Obtener autorización para entregar/instalar esa copia firmada exacta antes de hacerlo. No reutilizar una autorización de BetaDevelopment.

Completar este recibo antes de probar; un campo pendiente bloquea la instalación:

| Campo | Valor que debe completarse |
|---|---|
| Commit de corrección | Según informe final/PR separado |
| SHA-256 unsigned corregida | Según gate de la compilación nueva |
| Certificado SHA-256 autorizado | Pendiente de autorización; no existe firma realAlpha en esta entrega |
| SHA-256 y tamaño de la copia firmada | Pendientes; serán distintos del unsigned |
| Autorización de entrega e instalación | Pendiente, vinculada a la copia firmada y certificado anteriores |
| Modelo / versión / compilación Android | Completar desde Ajustes del teléfono |
| Paquete | `io.github.jose22yt.flexygram.realalpha` |

Comparar el SHA de la copia recibida con el recibo utilizando una función SHA-256 local ya disponible/autorizada en el teléfono. Si no está disponible, registrar esa comprobación como pendiente; no afirmar que se verificó. Verificar el certificado y la identidad en el recibo técnico antes de la instalación. No inventar una huella ni instalar una herramienta de terceros automáticamente.

## Preparación de la sesión, una vez autorizada

1. Registrar fecha/hora de inicio, orientación, tamaño de texto y navegación actual (gestos o tres botones). Anotar el modo claro/oscuro original para restablecerlo al terminar.
2. No tocar Telegram ni otras variantes ya instaladas. No borrar datos, exportar sesiones, importar backups o proporcionar números/códigos. Si ya existe realAlpha con este mismo paquete, detenerse para revisar su identidad; no actualizarla, borrarla o desinstalarla automáticamente.
3. Para una prueba controlada, poner temporalmente el teléfono en modo avión y comprobar Wi-Fi apagado; anotar cualquier excepción necesaria. Esto complementa el manifiesto sin INTERNET y los bloqueos Java/JNI, no demuestra ausencia universal de IPC. No modificar certificados del sistema ni protecciones de Android.
4. Solo después de la autorización, instalar la copia firmada exacta por el flujo normal del teléfono. No hay un comando o instalador automático en este documento. Si Android la rechaza, registrar el mensaje y detenerse; no desactivar Play Protect ni alterar políticas para forzarla.
5. No conceder permisos inesperados. La variante revisada solo declara ACCESS_NETWORK_STATE y su permiso interno de receiver protegido por firma; no debe pedir contactos, teléfono, cámara, micrófono, archivos o acceso a cuentas.

## Secuencia manual

Registrar cada caso como PASS, FAIL o BLOQUEADO. Una prueba no ejecutada no es PASS. Si aparece un cierre, login, solicitud de credenciales o salida a una aplicación externa, detener la secuencia y anotar el paso exacto.

| Caso | Pasos en el teléfono | Resultado esperado |
|---|---|---|
| T01 — Inicio | Pulsar el icono de realAlpha y observar durante 60 segundos | Inicio sin crash/ANR; pantalla nativa de diálogos vacía, sin login ni asistente de cuenta |
| T02 — Lista vacía | Inspeccionar lista, barra y estado vacío; desplazar suavemente arriba/abajo | Sin chats, mensajes, usuarios ficticios o contenido restaurado; respuesta normal de la interfaz |
| T03 — Atrás desde raíz | Ejecutar un Atrás; si sale al launcher, volver a abrir | Una única acción, sin doble salto, pantalla negra, bloqueo o crash; reapertura en lista vacía. Salir de la raíz puede ser el comportamiento original correcto |
| T04 — Cajón/búsqueda | Si existen, abrir cajón o búsqueda sin seleccionar login/chat; ejecutar Atrás | Cierra/cancela el elemento visible según Exteraless; no salta a Login/Sessions/Chat. Si el control no existe, dejar ese subcaso BLOQUEADO |
| T05 — Gestos cancelados | Con navegación por gestos ya habilitada, iniciar y cancelar cinco gestos de Atrás desde un elemento permitido | La interfaz vuelve al mismo estado de forma coherente; no ejecuta un Atrás completo al cancelar |
| T06 — Gestos consecutivos | Completar diez ciclos de abrir elemento permitido → Atrás; repetir desde ambos bordes si el sistema lo permite | Sin doble despacho, saltos inesperados, animación atascada, pantalla negra ni cierre. Si se sale de la raíz, reabrir antes del siguiente ciclo |
| T07 — Claro | Cambiar el tema del sistema a claro desde Ajustes y volver a realAlpha | Registrar el tema efectivo de la app y legibilidad de texto/iconos/fondo. Si no sigue el sistema, no declarar aprobado: registrar la configuración y dejar el cambio de tema de la app pendiente sin habilitar pantallas bloqueadas |
| T08 — Oscuro | Cambiar el tema del sistema a oscuro y repetir T02–T04 | Registrar tema efectivo, contraste y ausencia de fallos. El cambio del sistema por sí solo no prueba que el tema interno cambió |
| T09 — Segundo plano | Inicio → esperar 30 s fuera → volver por Recientes; repetir tres veces, una con pantalla bloqueada/desbloqueada | Lista vacía y respuesta normal; sin login, cuenta, contenido restaurado, bloqueo o crash |
| T10 — Orientación | Rotar y volver a la orientación inicial, si la pantalla lo permite | UI estable; no asumir recreación de Activity: el manifiesto puede manejar cambios de configuración directamente |
| T11 — Recreación | Solo si se acepta cambiar temporalmente una opción global de desarrollador: anotar el valor de «No conservar actividades», activarlo, salir al launcher y volver a realAlpha tres veces; restablecer inmediatamente el valor original | Retorno a raíz nativa vacía sin cierre ni identidad restaurada. Registrar el método; sin instrumentación no se certifica el número exacto de callbacks. Si la opción no está disponible o no se desea cambiar, marcar BLOQUEADO |
| T12 — Relanzamiento | En información de aplicación de realAlpha, usar «Forzar detención», sin borrar datos; volver a abrir y observar 60 s | Arranque limpio, misma raíz vacía, sin errores visibles. Esto prueba relanzamiento, no equivale a T11 |
| T13 — Cierre de sesión de prueba | Repetir T03 y volver una última vez a realAlpha | Sin crash visible, bloqueo o interfaz residual. Restaurar tema, conectividad y opciones globales modificadas |

No activar Glyph, plugins, herramientas debug, autenticación, restauración ni red. No buscar ni enviar mensajes, no abrir chats y no probar llamadas. No capturar pantallas de Recientes, notificaciones u otras aplicaciones que contengan datos personales.

## Qué devolver tras la prueba

Copiar esta tabla en un informe de texto privado:

| Dato | Resultado |
|---|---|
| APK firmada SHA / certificado autorizado | Pendiente |
| Modelo / Android / compilación | Pendiente |
| Navegación / orientación / tema efectivo | Pendiente |
| T01–T13 | Pendiente por caso, incluyendo subcasos bloqueados |
| Primer fallo: caso, acción, hora y mensaje literal sin datos personales | Pendiente |
| Reinicio/cierre inesperado, congelación o diálogo ANR observado | Pendiente |
| Opciones globales restauradas al final | Pendiente |

Si falla: registrar únicamente la pantalla de realAlpha o el texto del error, sin teléfono, cuentas o notificaciones personales. No exportar un bugreport completo del teléfono ni volcados de cuentas. El análisis posterior de logs deberá limitarse al paquete realAlpha y contar con autorización; este procedimiento no recopila logs automáticamente.

La prueba de Android 17 verifica la experiencia de ese dispositivo. **No demuestra compatibilidad API 24–32, funcionamiento en páginas de 16 KB ni los doce casos nativos/Python de laboratorio.** Tampoco una lista visualmente vacía prueba todos los slots de cuenta o la clase del fragmento: esas comprobaciones internas siguen requiriendo instrumentación revisada. No afirmar ausencia de crashes fuera de la ventana observada.

## Matriz Android que permanece pendiente

| Plataforma | Comprobación específica |
|---|---|
| ARM64 API 24–32 / 4 KB | Atrás heredado, arranque y carga/verificación de clases Glyph; teléfono Android 17 no cubre estos sistemas |
| ARM64 API 33 | Callback original, cinco cancelaciones/consecutivos y limpieza tras destrucción |
| ARM64 API 34+ | Callback predictivo original, cancelación, drawer y recreación |
| ARM64 / 16 KB real estricto | Carga JNI/Chaquopy sin fallback y casos nativos originales |
| Teléfono Android 17 del usuario | T01–T13, solo tras autorización de copia y certificado exactos |

Reutilizar el ejecutor de `tests/native_compatibility/android_lab` mediante un contrato realAlpha separado. El contrato Diagnostic, su certificado, alias y hashes no deben reutilizarse como si identificaran esta variante. Ninguna fila de esta matriz se ha ejecutado con este documento.
