# Pantallas nativas: flujo local preparado

Base fija: PR #39 `40faca6b04563bcacd02d0947addd4c18ff81e81`.
Código de la entrega inicial: `3a7ef7e6105eec1286e63c05fe1c7f858b92968c`.
Corrección posterior validada: `379131f15dba3a90ad0b48cb8c0af7b99938affc`.
Rama independiente `preparation/native-login-local-pages`, PR #40 en borrador.
FlexyGram: @Lukhou23; se mantienen código, créditos y licencias Telegram/Exteraless.

## Continuación: limpieza de campos originales

Se reprodujo un defecto del overlay preparado, no un fallo Android observado:
`CodeFieldContainer.setText("")` original recorre cero caracteres y deja los dígitos
existentes. `localClearPage` ahora borra cada editor y restaura en `finally` el valor
anterior de `ignoreOnTextChange`, evitando el watcher de autocompletado durante esa
limpieza. Tolera contenedor/array/campos ausentes y libera los metadatos locales.
No se modifica CodeFieldContainer ni LoginActivity originales.

Cinco regresiones usan los cuerpos originales sin modificar de ambos overloads
setText y el método exacto de limpieza del overlay; sólo los widgets son dobles.
Antes del fix: 4 fallos y 1 PASS; después: cinco PASS. Se repitió la suite afectada:
**42 distintas (37 anteriores +5 nuevas), normal y -O:84 ejecuciones PASS, cero
fallos/omisiones finales**. No se repitieron las otras 11 regresiones de la entrega
inicial ni se suman sus resultados como una nueva ejecución.
[IDs, comandos, hashes y logs](evidence/continuation/results.json).

Se actualizó el SHA del overlay en el inventario. Si existe una copia generada anterior,
el materializador la rechazará: conservarla fuera del destino generado antes de crear
la nueva; no sobrescribir el archivo compartido. El parche 0003 de Gradle no cambió.
Se comprobó además que mainExecutor usa Handler.post: la sospecha de un callback
inmediato antes de devolver el ticket no aplica a este adaptador y no se alteró esa ruta.

Siguen pendientes el typecheck completo con SDK37/dependencias/fuentes generadas,
AGP/Kotlin y ejecución Android. Esta continuación no ejecuta Gradle ni genera APK.

## Implementación

`telegram-login-local-ui` añade LocalLoginSession, EphemeralPages, NativeUiInput y
LocalTransitionFence. Usa AuthenticationController/LoginFlowOwner y el contexto TLRPC
de #39, con puertos locales y el mismo worker serial. No crea otra interfaz de login.
El canal contiene sólo página, longitud de código, disponibilidad de parámetros 2FA,
estado, consentimiento requerido y error enumerado. Teléfono/hash/SRP siguen en el
contexto efímero anterior; contraseñas/códigos no se guardan en Bundle ni preferencias.
El constructor requiere el ClosedRuntime realAlpha de #36; los puertos son contratos
internos de confianza, no un sandbox contra implementaciones maliciosas.

Los comandos poseen copias de entrada, se limitan por revisión/fase y token de vista,
y limpian sus buffers al ejecutarse, cancelar o separarse la vista. El propietario lógico
puede sobrevivir a la recreación; los renderers y comandos pendientes de la vista vieja
se invalidan. Un cambio de cuenta rechaza la nueva unión e invalida la anterior. No se
reproduce una solicitud al volver a unir la vista. Cancelar termina el flujo: otro intento
requiere un propietario nuevo y revisión explícita del diario, sin reinicio automático.

Se añade longitud de código al límite tipado existente: 0 significa desconocida y no
habilita la vista; valores fuera de 0–12 fallan cerrados. No cambia formatos de sesión.

## Matriz de integración offline

Ninguna fila está habilitada en una APK. «Candidata» significa adaptación y controles
host preparados; falta compilar y ejecutar la vista real Android antes de aprobarla.

| Vista original / número | Preparación local | Estado |
|---|---|---|
| PhoneView / 0 | Entrada sintética al controlador; bloquea SIM, nearestDc, países remotos, backend, permisos, passkeys y observador emoji | Candidata offline |
| LoginActivitySmsView APP / 1 | Longitud conocida; entrada local; sin observadores, timers, resend/cancelCode RPC ni Bundle | Candidata offline |
| LoginActivitySmsView SMS / 2 | Igual que APP; no lee SMS del sistema | Candidata offline |
| LoginActivityPasswordView / 6 | Metadatos efímeros; onShow obtiene parámetros sólo del puerto local; prueba/verificación por contexto #39 | Candidata; error SRP exige acción explícita |
| LoginActivityRegisterView / 5 | Nombres sintéticos; sin ImageUpdater, cámara, subida ni restauración | Candidata sólo sin términos pendientes |
| QR / 19 | No se construye ni acepta setPage; onShow/export/observadores bloqueados incluso ante llamada directa | Bloqueada |
| Call/flash/missed/word/phrase/email/Firebase/payment/recovery | Sin creación ni enrutamiento local; sin remapeo a SMS | Bloqueadas |
| Términos requeridos, privacidad externa, avatar, proxy, API personalizada y backend | No hay consentimiento ni proveedor revisado para este laboratorio | Bloqueados |
| Autorización simulada / persistencia incierta | Diagnóstico local; nunca onAuthSuccess, UserConfig ni borrado de sesiones | Sin entrada al cliente autenticado |

## Parches y copia de fuente para realAlpha

**No aplicar 0004 al LoginActivity compartido.** Referenciar clases exclusivas de
realAlpha desde main rompería la compilación de otras variantes. Se prepara una copia
de fuente comprobada por hashes en un directorio generado; el archivo original queda intacto.

- `0003-realalpha-local-pages-sources.patch` se comprueba/aplica sobre el Gradle original.
  Sin la propiedad nueva no cambia fuentes ni elegibilidad de las variantes. Con
  `flexygramLocalLoginPages=true` exige realAlpha, un overlay con SHA correcto y permite
  sólo realAlphaDebug en esa invocación. Excluye el LoginActivity de main y añade el
  overlay y los ocho directorios de módulos a realAlpha. No altera políticas o permisos.
- `0004-native-local-pages.patch` es un delta sobre la copia temporal con el binding
  #39. El materializador aplica ambos parches de UI en un temporal, comprueba el resultado
  y conserva una única copia generada. No se usa el parche Gradle 0001 de #39 como prerrequisito activo.
- El generador comprueba los originales contra el commit base fijo. El materializador
  rechaza contexto/hashes cambiados y un overlay existente diferente. No ejecuta Gradle.

La copia intercepta las entradas antes de las rutas originales. Además controla
constructores, callbacks de ventana, restauración y guardado, menú, permisos y eventos.
Se construyen sólo las cinco vistas permitidas y los bucles toleran las ranuras vacías.
Se desactiva el guardado automático de la jerarquía y el autofill de ese formulario.
Se reutilizan `flexygram_local_auth_restart` y `flexygram_local_auth_slot` del contrato #36.

Las transiciones conservan setPage, duración e interpolador originales. Sólo en el
overlay local se cancela la transición anterior y se comprueba su ticket de vista antes
de completar; separar la ventana invalida renderers/tickets, y destruir el fragmento
impide reactivarlo. No se propone un motor de animaciones ni una mejora de fluidez medida.

## Resultados y límites

[Resultados y comandos exactos](evidence/results.json): **37 pruebas nuevas + 11
regresiones seleccionadas = 48 distintas**. Normal y Python -O: **96 ejecuciones PASS**,
sin fallos/omisiones finales. Los logs de desarrollo conservan fallos resueltos y no se
suman a esos resultados. Se ejecutan Java real de los adaptadores y guardas extraídas
sin modificar del parche, con cuerpos de solicitudes originales y framework/RPC/storage
simulados. Se comprueban fuente JDK21 y símbolos SDK24; no se ejecuta criptografía SRP real.

Se ejecuta el bloque Groovy real con proveedores/sourceSets sintéticos: propiedad
apagada/encendida, realAlpha ausente, variantes ajenas y overlay manipulado. No es AGP.
El parser Java lee el LoginActivity parcheado completo **sin análisis de tipos**: acredita
sólo sintaxis. No se compiló el cliente completo, no se ejecutó Android y no se generó APK.
SDK37/classpath original y fuentes generadas siguen pendientes en este entorno, según #39.

Dos problemas concretos resueltos: el primer adaptador local comprobaba el estado del
transporte para permitir commit, aunque el controlador lo cierra al autorizar localmente;
ahora exige LOCAL_AUTHORIZED del controlador. Además se evita el fallo de aislamiento de
compilación usando el overlay en vez de modificar main. El constructor original PhoneView
incluye una solicitud nearestDc: también queda bajo el guard local, no sólo onNextPressed.
No son fallos Android reproducidos ni evidencia sobre el incidente previo de sesiones.

## Traspaso a Work 2 después de validar P1/P2

1. Revisar la cadena #35/#36/#38/#39 y los dos commits de este PR. No tocar PR #37/APK/firma.
2. Usar el attestor y puente JNI de sólo lectura #36 para construir ClosedRuntime;
   mantener API ID0/hash vacío y todas las capacidades cerradas. Crear puertos locales
   revisados, store/journal #38, contexto/transport #39 y LoginFlowOwner.
3. Crear LocalLoginSession con ese propietario/contexto/transporte y **el mismo worker
   serial**. Unirlo mediante bindClosedLocalPages antes de onFragmentCreate/createView
   del LoginActivity original. La vista se une/separa con la ventana, sin retener Activity
   en el propietario. Mantener parámetros privados fuera de la jerarquía/Bundle.
4. Ejecutar `python3.11 tools/native_login_pages/materialize_overlay.py`; verificar
   receipt.json y SHA. Aplicar sólo el parche Gradle 0003 en una rama de integración
   revisada y comprobar sourceSets con SDK37. El overlay no se publica como cliente.
5. Preparar una compilación futura con `-PflexygramRealAlpha=true
   -PflexygramLocalLoginPages=true`. Aún falta verificar AGP/Kotlin, exclusión efectiva
   del original, ausencia de clases duplicadas y puente JNI. No hay autorización de
   firma/instalación/distribución en esta misión.
6. En Android autorizado comprobar las cinco vistas, sistema Atrás, IME, temas,
   entrada/salida, recreación, callbacks y animaciones reales. Hasta entonces no certificar
   ciclo de vida Android ni habilitar QR, términos, servicios o autenticación real.

No se modificó ningún archivo activo de TMessagesProj, Gradle, manifests/JNI, políticas,
main/develop o PR #37. No hubo conexión Telegram, servicios externos, claves ni fusiones.
