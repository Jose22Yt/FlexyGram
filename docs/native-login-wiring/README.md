# Integración Android del login — preparación local

Base: PR #38 `19b515e0ce63bdecae235b434ca265dbaf4d48ca`.
Código final: `f8abf084fa4a6ae68541dc04d199417a1df0ebc2`.
Rama independiente: `preparation/native-login-android-wiring`, apilada sobre #38.
FlexyGram: @Lukhou23. Se conservan procedencia, créditos y licencias Telegram/Exteraless.

## Código entregado

`telegram-login-wiring` no está registrado ni empaquetado en ninguna variante activa.

| Componente | Función implementada |
|---|---|
| TelegramRequestContext | LocalRpc para NativeLoginTransport; crea los tipos originales sendCode, signIn, getPassword, checkPassword, signUp, export/importLoginToken |
| OriginalSrpLocalProof | Delega en SRPHelper.getX/startCheck originales; no implementa otro algoritmo ni abre conexiones |
| NativePagePlan | Relaciona estados tipados con los números originales de página; distingue ruta preparada de permiso para ejecutar su ciclo de vida |
| LoginNativeBinding | Reutiliza LoginActivityAdapter, propietario y relay anteriores; attach/detach, entradas locales, acciones intermedias y marcador de recreación |
| compile_originals.py | Intenta compilar fuentes originales completas, conserva comando/log/hashes y devuelve error cuando la compatibilidad está bloqueada |

El contexto exige realAlpha cerrado, puertos LOCAL_SIMULATION, cuenta coincidente y
el mismo lease de operación que TelegramAuthorizationStore. No incluye un puerto
ConnectionsManager. Todas las solicitudes construidas llevan API ID 0/hash vacío;
codeSettings no activa Firebase, llamadas, recuperación de tokens ni logout_tokens.
No hay preferencia, Intent o configuración remota que abra capacidades.

Se conserva temporalmente teléfono sintético/hash de código, parámetros SRP y copias
de tokens QR. Un único vuelo selecciona la primera respuesta tras validar su handle;
duplicados, callbacks antiguos, reentrada y cuentas/leases ajenos se rechazan. La
cancelación libera datos propios y cancela exclusivamente el handle local. Los errores
terminales limpian el contexto; reintentos autorizados conservan sólo el contexto
necesario. La consulta QR comprueba caducidad sin temporizador ni nueva solicitud.
Los String/TL prestados se liberan por referencia: no se garantiza borrado físico del heap.

**Defecto nuevo reproducido y corregido:** el contexto inicial retenía directamente
el Password del callback. Una mutación posterior cambiaba srp_id/srp_B del intento.
Ahora posee una copia de los parámetros usados por SRPHelper y limpia sus buffers
sin alterar los del proveedor. La regresión fallida previa se conserva como evidencia.
No se atribuye este defecto local a Telegram original ni a un fallo Android observado.

## Dos parches separados, sin aplicar

1. `patches/native-login-wiring/0001-realalpha-source-integration.patch` añade siete
   directorios Java sólo a sourceSets.realAlpha cuando esa variante ya está habilitada.
   Evita una dependencia circular biblioteca→aplicación, pues los adaptadores consumen
   clases del cliente. No modifica settings, permisos, credenciales, políticas ni JNI.
2. `0002-native-fragment-local-binding.patch` añade binding explícito al LoginActivity
   original antes de createView; publica el plan de página, mantiene la navegación
   original, desconecta la vista al destruir el fragmento y guarda sólo el marcador de
   reinicio. Con binding omite la restauración de logininfo2. **No intercepta todavía
   los botones/RPC originales ni habilita las páginas parametrizadas.**

Se aplicaron ambos parches únicamente a copias temporales durante las pruebas. Los
métodos añadidos del fragmento se compilaron y ejercitaron con framework/host dobles;
el bloque Gradle se ejecutó con Groovy para variantes habilitada/deshabilitada.
Los cuatro parches de seguridad #35/#38 permanecen intactos y sin aplicar al cliente.

## Bloqueos concretos de la interfaz original

En LoginActivity original del commit base:

- `LoginActivityQrView.onShow`, líneas 8536–8540, llama exportLoginToken(true).
  Esa ruta hace cleanup(false) en 8569 y usa cuentas existentes; no es una vista pasiva.
- `LoginActivitySmsView.setParams`, desde 4422, registra observadores de SMS/llamada
  y prepara timers; fillNextCodeParams (1946–2010) no es un simple cambio de pantalla.
- PasswordView.setParams (5623) espera parámetros nativos y lee contraseña/SRP de
  Bundle; RegisterView.setParams (8354) espera teléfono y phoneHash.
- Los botones originales conservan sendRequest, SRP y onAuthSuccess originales.

Por eso NativePagePlan identifica APP/SMS/CALL/FLASH/MISSED/WORD/PHRASE, PASSWORD,
REGISTER y QR, pero bloquea entrar en ellas hasta adaptar parámetros y efectos. El
parche sólo permite conservar la página o dirigir a PHONE sin parámetros. No crea una
interfaz falsa ni entrega una pantalla de autenticación funcional. Esta limitación es
deliberada y debe resolverse antes de activar el binding en una prueba Android.

## Validación real y alcance

Resultados finales y comandos: [evidence/results.json](evidence/results.json).

- **34 pruebas nuevas + 11 seleccionadas anteriores = 45 distintas**, ejecutadas con
  Python 3.11 normal y -O: **90 ejecuciones PASS**, cero fallos/omisiones finales.
- JDK21 compila adaptadores, cuerpo original completo de 14 clases de solicitud/tipos
  auxiliares, TLMethod/InputSerializedData/OutputSerializedData/TLDataSourceType y
  SRPHelper sin modificar. Se ejercitan los serializadores de solicitudes con un sumidero
  de valores de prueba, no con sockets ni un parser de red. Las respuestas TL y Android
  siguen usando proyecciones/dobles expresamente documentados en fixtures.py.
- El wrapper SRP se prueba con parámetros inválidos y fallos controlados. Compilar
  SRPHelper y comprobar su padding no demuestra interoperabilidad criptográfica real.
- Compilación de símbolos SDK24 y fuente JDK21 aprobadas; no son D8 ni ejecución Android.
- La compilación **completa** de LoginActivity, TLRPC, TL_account, UserConfig,
  AccountInstance, MessagesStorage, ConnectionsManager y SRPHelper se intentó con el
  árbol Java original completo. Está **BLOQUEADA** por classpath incompleto: aquí sólo
  existe android.jar API24; faltan SDK37, AndroidX y clases generadas/dependencias
  Kotlin y del cliente. Ver full-original-attempt/receipt.json y javac.log. Los errores
  de dependencias no se presentan como defectos del código ni como una compilación PASS.

No se ejecutó Gradle, APK, D8 ni Android. No hubo JNI/MTProto real, credenciales,
solicitudes Telegram, firma, instalación, distribución, workflows o fusiones.

## Traspaso preciso a Work 2 tras P1/P2

1. Integrar/revisar la cadena #35→#36→#38 antes de estos dos commits funcionales:
   `deec4ded5e1733c300ea4cef8101340351efc82d` y
   `f8abf084fa4a6ae68541dc04d199417a1df0ebc2`. No modificar su rama durante su build.
2. Revisar contexto/hashes y ejecutar git apply --check sobre cada parche, en una
   rama de integración. No aplicarlos automáticamente ni fusionar estos PR.
3. Construir store/journal locales de #38, TelegramRequestContext con LocalPort de
   laboratorio, transport=store.localTransport(runtime,context,clock) y LoginFlowOwner.
   Enlazar transport.bindLocalStateSignal(owner::signalLocalAdapterState). Pasar el
   mismo worker serial a LoginNativeBinding; conservar propietario, no Activity, al recrear.
4. Completar el parche de UI: redirigir PhoneView/SmsView/PasswordView/RegisterView
   a acciones locales; pasar parámetros originales mediante un canal efímero revisado;
   impedir observadores, timers, cleanup y export nativos desde el QR local. No quitar
   los bloqueos de NativePagePlan hasta probar cada rama. No persistir esos datos en Bundle.
5. Integrar por separado el puente JNI de sólo lectura preparado en #36 y la persistencia
   original verificable de #38. El source-set patch no incorpora el C++ ni autoriza writes.
6. Con SDK37, classpath original y fuentes generadas disponibles, repetir:
   `python3.11 tools/native_login_wiring/compile_originals.py --output <directorio-nuevo> --classpath <classpath-revisado> --generated-source <fuentes-generadas>`.
   Después hace falta el build Android completo realAlpha y pruebas de ciclo de vida.
7. Mantener las capacidades cerradas. El transporte remoto, las credenciales propias,
   las ramas email/Firebase/payment/recovery, los logs originales y la seguridad de
   persistencia necesitan revisión y autorización separadas antes de una cuenta real.

PR #34, #38, main/develop y las variantes/APK anteriores no se modificaron.
