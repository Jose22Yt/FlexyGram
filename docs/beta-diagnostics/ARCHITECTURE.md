# Hallazgos concretos y puntos de medida

Base de código inspeccionada: `b637c290c4514f158196ae7e5db3ba7daf7ed4c2`.
Las referencias de línea corresponden a esa base. Un solo cambio runtime,
NotificationCenter:538. Lo demás son observaciones para Work2, sin optimizaciones.

| Prioridad / estado | Archivo, método y línea | Hecho y verificación posterior |
|---|---|---|
| Alta / defecto de callback confirmado por Java | `org/telegram/messenger/NotificationCenter.java:512–538`, checkForExpiredNotifications | Al quedar una animación joven, la reprogramación entregaba una lambda que asigna un método en vez de ejecutarlo. Prueba real del cuerpo Java con dobles: original no expira la segunda entrada; corregido sí. No se afirma incidencia/frecuencia Android |
| Alta / espera confirmada; impacto no medido | `org/telegram/ui/ChatActivity.java:3106–3113,3145–3151,3182–3188,3200–3206`, onFragmentCreate | Cache misses de chat/user/encryptedChat publican lectura en StorageQueue y esperan CountDownLatch sin timeout. Medir espera/cola/UI con caché fría; no afirmar deadlock o lentitud general |
| Alta / política de navegación confirmada | `org/telegram/ui/ActionBar/ActionBarLayout.java:1070,1515,2446,3101` | Intercepción/gestos y presentFragment guardan transiciones activas/animationInProgress/startedTracking. Retorno false debe separarse de request aceptado. No eliminar guardas como optimización improvisada |
| Media / recuperación temporal, riesgo pendiente | `ActionBarLayout.java:2126–2133,2645,2680` | checkTransitionAnimation utiliza currentTimeMillis y umbral1500ms; preview tiene tratamiento propio. No es un retraso de1500ms aplicado a cada apertura. Cambios de reloj son hipótesis a probar, no fallo demostrado aquí |
| Media / cancelación existente | `ActionBarLayout.java:2058–2109` | onAnimationEndCheck cancela Runnable/Animator/Spring al recuperar y restablece transformaciones. Medir cancelación y destino final antes de tocar este código |
| Media / punto de sincronización | `ChatActivity.java:29046–29115`, onTransitionAnimationStart/End | Se registran animaciones en NotificationCenter, se actualiza visibilidad y se equilibran notificaciones al terminar. Instrumentar con IDs opacos, no dialog_id |
| Media / posible ráfaga de trabajo | `NotificationCenter.java:490–507,549–580` | Se posponen notificaciones y se liberan juntas al terminar animaciones. Medir longitud/procesamiento de delayedPosts; no se ha medido que sea costoso |
| Media / construcción y asignaciones | `ChatActivity.java:4029,7121,8525`, createView/ChatActivityAdapter/ChatActivityEnterView | Creación de vista, adaptador y entrada de chat son puntos para medir UI/alloc. `MessagesStorage.java:18345–18404` construye listas en lecturas cache-miss. Existir asignaciones no demuestra presión de GC ni que convenga cachearlas |
| Baja / entrada a ruta | `DialogsActivity.java:8410–8416` y otras ramas de apertura | checkCanOpenChat precede presentFragment/new ChatActivity. No asumir que todas las rutas pasan por una sola rama; escenarios de búsqueda, temas, bots y gestos requieren cobertura propia |

## Corrección aplicada

```diff
- AndroidUtilities.runOnUIThread(() -> checkForExpiredNotifications = this::checkForExpiredNotifications, Math.max(17, time));
+ AndroidUtilities.runOnUIThread(checkForExpiredNotifications = this::checkForExpiredNotifications, Math.max(17, time));
```

La expresión corregida conserva el Runnable que realmente se publica, como ya
hace la programación inicial en línea506. No cambia5017ms, el criterio interno
de1000ms, callbacks normales de animación, allowedIds ni heavyOperationsCounter.
Al reejecutarse el método, su primera instrucción vuelve a limpiar la referencia.

Regresión: `test_notification_expiry.py` obtiene el cuerpo original con git show
del commit19200e8 y el cuerpo corregido del checkout. Verifica que la única
diferencia es esa expresión. Compila ambos con JDK21 y ejecuta el mismo escenario:
una entrada vieja y otra joven. La primera comprobación expira sólo la vieja;
el callback posterior original lanza EXPIRY_CALLBACK_NOT_EXECUTED; el corregido
expira la joven y conserva/limpia correctamente la referencia programada.

Son el método Java real y dobles mínimos de reloj/cola/tabla. No es una
compilación Android de NotificationCenter completa, ni prueba de todas las
notificaciones, minSdk, memoria o rendimiento. Falta validación de integración
Android y de escenarios de cancelación/lifecycle en la futura beta.

## Lo que no se corrigió por suposiciones

No se introdujeron timeouts en lecturas de datos: podrían cambiar la apertura
legítima. No se eliminaron guardas, animaciones, blur, callbacks de lifecycle ni
funciones. No se cambiaron relojes de la navegación ni se prometió respuesta
instantánea. Work2 dispone de puntos de observación y una corrección acotada
para revisión independiente. Medir CPU, waits/IO, colas y GC en trazas autorizadas
antes de decidir otra modificación.
