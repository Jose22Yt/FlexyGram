# Próxima prueba exclusivamente con teléfono

**Pendiente de nueva firma, entrega e instalación autorizadas por SHA-256 y certificado. No ejecutar estos pasos sobre un binario no aprobado.** La versión unsigned diagnóstica no es instalable sin firma. No usar la clave temporal perdida ni desinstalar la realAlpha anterior.

## Lo que se puede hacer ahora

Conservar la APK que falló, sus datos y el video. No borrar almacenamiento, no restaurar cuentas, no abrir opciones de envío de informes del sistema. El video confirma el síntoma, pero no proporciona stack ni señal nativa. No hay una vía verificada para extraer el fichero privado de la app ya instalada desde otra app sin ADB/root o un exportador implementado en esa misma app. Android no permite que el futuro diagnóstico lea el UID anterior. No se solicita bugreport general ni datos de otras apps.

## Después de autorizar una nueva copia diagnóstica concreta

1. Descargar desde el destino privado autorizado. Comprobar SHA/certificado del recibo; aprobar su instalación separadamente. La etiqueta será **FlexyGram Startup Probe**, paquete `io.github.jose22yt.flexygram.realalpha.startupdiagnostic`. Conservar instalada la realAlpha afectada.
2. Para la prueba, poner el teléfono en modo avión y desactivar Wi-Fi. No crear cuentas, introducir claves Telegram o importar archivos. No cambiar datos/permisos de Telegram u otras variantes.
3. Abrir **Startup Probe**. Debe verse primero la pantalla mínima de diagnóstico, no una pantalla negra. Si esta pantalla ya falla, registrar solo ese síntoma/video: no atribuirlo a DialogsActivity.
4. Pulsar **Ejecutar un arranque nativo** una vez. Observar si aparece la lista nativa vacía, negro/escritorio, diálogo de cierre o congelación. No repetir en bucle ni borrar datos para cambiar el resultado.
5. Si vuelve al escritorio, abrir de nuevo **Startup Probe**. Pulsar **Actualizar informe**. El proceso de informe evita inicializar Telegram; puede recuperar el diario del probe y, en Android17, su motivo de salida si Android lo conservó.
6. Pulsar **Copiar informe sanitizado** únicamente si se desea facilitarlo para revisión. Pegar ese texto manualmente en este chat. Contiene etapas, categorías, alias de clase/línea y motivo/status del proceso propio. No adjuntar logcat, bugreport o carpetas privadas. La copia al portapapeles es explícita; no se envía automáticamente nada.
7. Si el probe sigue vivo, volver mediante Atrás y consultar el informe. El botón no inicia otro probe mientras detecta su proceso activo. Si hace falta otro intento frío, primero conservar el informe y usar **Forzar detención solo de Startup Probe** en Ajustes > Apps; nunca Borrar datos ni desinstalar. Volver a abrir el diagnóstico y repetir una vez. No forzar detención de Telegram ni de la realAlpha afectada.
8. Facilitar resultado y última etapa: pantalla mínima visible sí/no; lista nativa visible sí/no; retorno al informe/escritorio; texto sanitizado. No interpretar FIRST_DRAW como éxito de la lista sin observarla.

## Solo después de confirmar la causa y aprobar una corrección

Repetir en una APK corregida autorizada: arranque frío tres veces; lista vacía y sin login; Atrás por botón y gesto; cancelación del gesto predictivo y cinco gestos consecutivos; claro/oscuro; segundo plano y regreso; rotación/recreación; nueva apertura tras cierre del proceso. Conservar informe de cada fallo. No habilitar red para resolver una pantalla negra. La prueba de estabilidad no sustituye el diagnóstico inicial.

Los datos de un paquete diagnóstico separado no modifican ni restauran datos de realAlpha/Telegram. No existe todavía aprobación de ejecución de esta variante ni una firma nueva.
