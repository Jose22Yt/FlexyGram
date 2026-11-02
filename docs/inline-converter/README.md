# Inline Smart Converter 1.0 — candidato nativo

Base comprobada: `feat/beta-official-source-v2`, `abf93053f9f98bae95b88f070f3e964c8b3bb311` (posterior a la referencia bdaafa). Rama independiente `feat/inline-smart-converter`. No sustituye la fuente Beta ni integra automáticamente otros PR. Sin APK, cambios de paquete, firma, versión o entrega privada.

## Implementación

| Componente | Responsabilidad |
|---|---|
| InlineConversionScanner | Patrones precompilados, posiciones UTF-16, números regionales y exclusiones |
| UnitConversionEngine | Millas/km, libras/kg, pies/metros, pulgadas/cm y temperaturas explícitas con BigDecimal |
| TimeConversionEngine | IANA, fechas, cambios de día y DST; devuelve huecos y horas repetidas sin ajustarlos silenciosamente |
| ExchangeRateProvider | Contrato desacoplado; ninguna implementación ni consulta de red |
| InlineConversionController | Preparación en globalQueue existente, caché RAM limitada, generaciones y gestos |
| InlineConversionPopover | PopupWindow del cliente, Copiar/Cerrar, fecha y elección de zona/offset cuando corresponda |
| InlineConversionSettingsSection | Siete controles reales directamente en Chat, con selectores reciclables |

La referencia del propietario `InlineMatchScanner.java` del ZIP se utiliza como punto de partida conceptual. No se incorpora su implementación Android inexistente ni se atribuyen sus pruebas aisladas a una ejecución del cliente.

El renderizador y los spans originales se conservan. ChatMessageCell consulta el conversor después de selección, spoilers, enlaces, captions, multimedia, reacciones, respuestas y controles administrativos. Usa las mismas coordenadas, bloques, offsets UTF-16 y corrección RTL que Telegram. No sustituye MessageObject ni crea URL artificiales. Long press conserva el temporizador/menú nativos. Cancelar, desplazarse, multitouch, reciclar o separar la celda descarta el gesto; generaciones y referencias débiles descartan resultados obsoletos. El popup se elimina al desplazarse, cambiar geometría de ventana o separar la celda.

Los textos EN/ES/RU usan recursos y los controles/popup usan colores del tema. No se añaden animaciones por fila, hilos propios, sondeo, sockets, bitmaps, blur, registros de mensajes ni permisos.

## Límites deliberados y aceptación pendiente

- Opt-in inicialmente desactivado. La primera preparación se hace al bind/attach; si aún no está disponible, el toque conserva la ruta nativa. Después de activar/cambiar los ajustes sobre celdas ya presentes, un primer toque puede preparar la detección para el siguiente. No se consume el toque esperando un trabajo asíncrono.
- 4096 unidades UTF-16 por cuerpo/caption; textos más largos se omiten completos. Máximo 12 coincidencias, 36 candidatos por familia y 128 spans/rangos. La caché LRU tiene 32 entradas, sólo RAM. Su clave incluye cuenta, diálogo, mensaje, edición, texto exacto, exclusiones, idioma y revisión de ajustes. No se registra/transfiere esa clave.
- Los números siguen el locale de la interfaz. `250.000 COP` significa 250000 en es-CO; no se adivina otra región del remitente. ISO en mayúsculas obligatorio para evitar convertir palabras como «all» en moneda. `$45` sin código no identifica una divisa.
- Se omiten código, spoilers, citas con geometría especial, richLayout, vistas previas, patrocinados/efímeros y selección activa. Los captions simples sí usan sus bloques nativos. `m` e `in` aislados se omiten por ambigüedad; utilizar `metros`, `feet`, `inches`, etc. No se añade conversión a los controles de accesibilidad de enlaces: con lector de pantalla permanece el comportamiento nativo; acceso específico por TalkBack pendiente.
- EST/EDT/PST/PDT se interpretan como offsets explícitos -05/-04/-08/-07, mostrados junto al original. Para reglas regionales usar un identificador IANA. CST/IST requieren elegir una zona; luego se usan sus reglas IANA. Horas inexistentes se advierten; repetidas exigen elegir offset.
- Sin fecha en el mensaje se usa la fecha del envío en la zona de origen y se muestra ese supuesto. El selector nativo permite cambiarla; una fecha elegida se etiqueta como tal. No se interpretan frases relativas («mañana»).
- El popup se limita al área visible de ventana/lista, padding y reservas conservadoras para cabecera/pin/composer. No es una prueba de insets de todos los diseños: teclado, pins, multiventana, fuentes grandes, rotación y RTL requieren aceptación física. Su contenido puede desplazarse si falta altura. No utiliza permisos de overlay.
- No hay proveedor de divisas autorizado. Se muestra origen/destino y «tasas no disponibles» sin resultado monetario ni botón Copiar. No se simula carga/cotización. No se conectará un proveedor sólo porque este PR se integre.

## Ajustes y persistencia

Ruta única: **FlexyGram → Chat → Mensajes e interacción → Conversiones rápidas** (sección directa junto a los controles existentes de interacción).

| Clave nueva en NekoConfig.getPreferences() | Valor inicial |
|---|---|
| flexy_conversion_enabled | false |
| flexy_conversion_currency | true |
| flexy_conversion_target_currency | Moneda regional; USD sólo como selección inicial si no existe región |
| flexy_conversion_time | true |
| flexy_conversion_target_zone | Vacío: zona del dispositivo |
| flexy_conversion_units | true |
| flexy_conversion_unit_system | 0: automático; 1: métrico; 2: imperial |

Automático utiliza la región del idioma de la interfaz: US/LR/MM imperial, resto métrico. Las selecciones explícitas prevalecen. SharedPreferences.apply actualiza memoria y persiste de forma asíncrona. Snapshot inmutable evita lecturas de disco por frame. No se renombran preferencias anteriores, no se tocan cuentas/sesiones y no hay recreaciones globales. El cambio de destino invalida la revisión preparada, sin recargar chats ni mover el scroll.

## Pruebas reproducibles

```sh
python -m pytest tests/test_inline_converter.py -q -s
# Con los submódulos fijados disponibles:
python -m pytest tests -q
python tools/signing/check_verifier.py
python tools/connected_alpha/run_checks.py
python tools/identity/check_identity.py
python -m unittest discover -s tools/connected_alpha -p test_performance.py -v
```

Los tres últimos controles conservan sus restricciones originales. Los bloqueos heredados se detallan en `results.json`; no se amplían listas de archivos aprobados ni se desactivan verificaciones para hacerlos pasar. El workflow específico ejecuta núcleo/hosts y verificador de firma sin secretos; no equivale al pipeline de APK.

Java puro se compila y ejecuta realmente. Controller/config se compilan y ejecutan contra dobles explícitos de colas, vistas, preferencias, tiempo y spans; eso permite detectar generaciones obsoletas, cancelación, exclusiones y valores guardados, pero no acredita lifecycle Android ni durabilidad física del almacenamiento. JavaParser acredita sintaxis, no resolución de APIs o compilación completa.

## Integración y reversión

1. Revisar el PR sobre abf930 y resolver manualmente cualquier avance de Work 1 en ChatMessageCell o SignatureDirectSettingsActivity. Conservar intactos los handlers nativos; el cambio añade un hook después de ellos y preparación/limpieza de celda.
2. Con JDK21, API37, Build Tools36, NDK/submódulos originales y entradas Beta autorizadas, ejecutar `NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:compileBetaJavaWithJavac` y el pipeline Beta completo habitual. No omitir JNI/Chaquopy ni controles de seguridad. No entregar una APK desde este laboratorio.
3. Ejecutar las pruebas físicas indicadas en `PHYSICAL.md`, capturar ambos temas con mensajes de prueba y comprobar ausencia de regresiones antes de integrar/entregar.
4. Si aparece un problema táctil, desactivar el ajuste general devuelve la ruta nativa inmediatamente. Para revertir código, revertir el commit completo de este PR: no modificar manualmente el almacenamiento existente ni borrar datos. Las nuevas claves pueden quedar guardadas, inertes.

La compilación integrada y las capturas reales están pendientes; no se presenta este candidato como validado físicamente.
