# CRASH-001 — conversación sintética sin cuenta

## Evidencia y límite de la conclusión

El responsable reprodujo en su Android el cierre del proceso al pulsar
Synthetic conversation en la APK del commit
`97dfb08e58159b31d322dd8435080fb039abdeb9`.
No se recibió una excepción/stack trace y esta sesión no dispone de ejecución:
`No usable execution environment is available`.
No se reprodujo el cierre desde esta sesión ni se inspeccionó el vídeo.

Hechos de fuente en ese commit:

- `BetaPreviewActivity.Conversation.createView()` instancia
  `ThemePreviewMessagesCell(context, navigation, 0)`.
- `ThemePreviewMessagesCell.java:88,204–274,292,435` utiliza
  `UserConfig`, construye `MessageObject` y `ChatMessageCell` y asigna mensajes.
- `ChatMessageCell.java:2013` obtiene un observer de
  `DownloadController.getInstance(currentAccount)`; su método
  `updateCurrentUserAndChat()` consulta `MessagesController` y `UserConfig`.
- `MessageObject.java:2082–2135` inicializa recursos de mensajes, consulta
  `UserConfig` y procesa texto/emoji.

Esto confirma una dependencia inadecuada para una fixture aislada. **No identifica
la excepción que terminó el proceso**: un usuario nulo/ID cero no prueba por sí
solo un NullPointerException. No se atribuye el incidente a una cuenta ni a JNI.

## Cambio acotado

Sólo la conversación de betaDevelopment usa `OfflineConversationView`:
tres mensajes fijos, burbujas entrantes/salientes, indicación Local, fuente
del sistema y paleta clara/oscura. Su construcción sólo importa APIs framework.
No consulta controladores de Telegram, almacenes de cuenta, fuentes externas,
MessageObject, medios, emoji, JNI ni Python. No oculta excepciones.

Se conservan `BetaNavigation`, LatestNavigation, presentFragment, la cola,
el callback Atrás moderno, observaciones y animaciones de ActionBarLayout.
ThemePreviewMessagesCell/ChatMessageCell y las funciones de producción no se
alteran. El sondeo Local Python sigue siendo una operación explícita de Ajustes.

Base del parche: HEAD verificado de PR #23,
`090b907cfd305614130fe35340bd148bc247dcff`.
Su Activity coincide exactamente con el commit instalado. PR #23 y la APK
firmada permanecen intactos. El PR se dirige a su rama para mostrar sólo este
parche, sin integrarlo automáticamente. PR #31/#32 no se modifican; al incorporar
la exportación futura de #32, aplicar este diff, no copiar una Activity completa.

## Regresiones preparadas, no ejecutadas

`test_offline_conversation.py` compila wrappers Java reales con dobles framework.
Su sustituto de ThemePreviewMessagesCell lanza un error si se invoca; UserConfig
rechaza sesiones y JNI/Python se declaran no disponibles. Esto comprueba el
aislamiento en el host cuando se ejecute, **no reproduce el fallo Android**.

Nueve casos (incluidos dos del commit de insets): abrir/volver sin cuenta, contenido sin runtimes opcionales,
25 ciclos, toques rápidos/Atrás durante transición, temas claro/oscuro,
recreación, ausencia de imports de cuenta/runtime en la vista, redispatch de
insets/IME y cabeceras sin doble margen.
No se omiten pruebas cuando falta JDK: fallan por requisito ausente.

Pendiente en un host con Python 3.11 y JAVA_HOME=JDK21:

```sh
python3.11 -m unittest discover -s tests/beta_development -p test_offline_conversation.py -v
python3.11 -O -m unittest discover -s tests/beta_development -p test_offline_conversation.py -v
```

Después ejecutar la suite beta existente con sus requisitos Gradle/CMake
originales y compilar `:TMessagesProj:assembleBetaDevelopmentDebug` ARM64,
JNI/Chaquopy completos y sin firma; aplicar los verificadores existentes.
No se ha hecho en esta sesión: **0 pruebas ejecutadas; compilación pendiente**.

Para aceptar el arreglo hace falta una nueva APK identificada por su hash,
verificación offline y las autorizaciones separadas de firma/entrega/instalación.
La APK actual no cambia al publicar este parche. En el teléfono: abrir demo,
volver, repetir, Atrás durante apertura, alternar tema y recrear/reabrir Activity.
Confirmar que no termina el proceso y que hay contenido. Capturas/grabación
permiten reportar el resultado; un cierre persistente requiere evidencia de
excepción disponible por un mecanismo autorizado, sin exigir ADB al usuario.

## Insets, commit separado

El host de beta ahora envuelve ActionBarLayout en un FrameLayout que aplica
systemBars/displayCutout mediante AndroidX existente. Devuelve los insets
restantes para mantener el tratamiento de IME por ActionBarLayout.
Las tres cabeceras desactivan occupyStatusBar: una sola capa posee el margen.
El padding es absoluto, se sustituye al redispatch y no se acumula.

No se cambia el manifiesto, flags de ventana, gestos ni motor de navegación.
Los dobles sólo prueban aritmética y configuración de cabeceras, no el despacho
real de ventanas ni la apariencia en Android 17. Pendiente comprobar gestos,
recortes, rotación y ambas paletas en el dispositivo. Este segundo commit puede
revisarse/aplicarse por separado sin retrasar el parche de la conversación.
