# Resultado ejecutado — beta offline, 2026-10-20

Proyecto creado y dirigido por @Lukhou23. PR23, rama `development/beta-offline-foundation`.
No es una beta autenticable, ni funcionamiento Android validado.

## Trazabilidad y separación

- Integración Work1/PR22 preservada en PR17: `19200e843cc9bf31c27a99e7b6775494627b131e`.
  Reejecución independiente: **367/367 métodos distintos**, Python3.11.17 normal y `-O`,
  cero omisiones/fallos/errores. 318 nativos +49 de laboratorio; los34 solicitados
  están incluidos. No sumar ambas modalidades ni adjudicar estos resultados al código beta.
- PR17: commit documental `b637c290c4514f158196ae7e5db3ba7daf7ed4c2`, sin cambios beta.
- Beta: `643566b46b8aaf41033e1e059805379dde737cf7` introduce el flavor y cliente offline.
- **Código exacto compilado final: `525b699982610b0d3721f85123734ae6b73154e8`**.
  Sus17 archivos de aplicación/Gradle/JNI fueron comparados byte a byte, con la única
  transformación privada reproducida por la receta experimental preexistente.
  El commit posterior de revisión añade herramientas, corrección del init-script y evidencias;
  no se presenta como nueva compilación del cliente.
- PR23 se apila sobre la rama de PR17 para mantener pequeño el delta. No fusionado.
  main/develop sin cambios; PR2 abierto. Los contratos/pins históricos se conservan.

## Código y errores realmente corregidos

Perfil `betaDevelopment` opt-in, Debug/ARM64, paquete independiente
`io.github.jose22yt.flexygram.beta.development`, API ID0/hash vacío, seis capacidades
externas false. Se conserva el código común y las políticas protegidas Diagnostic/Production.
Fachada beta independiente; el grafo real no incluye el módulo Diagnostic ni el AAR retirado.
Las rutas sintéticas usan DialogCell, ThemePreviewMessagesCell, TextSettingsCell,
ActionBarLayout y Theme; Python local se inicia bajo demanda fuera del hilo UI,
sin motor de plugins. No se simula una sesión Telegram.

1. ActionBarLayout podía borrar una referencia nueva creada durante un callback síncrono.
   Se conserva la referencia nueva; el método histórico falla en el arnés Java real y el
   corregido pasa. No se cambian duración/curvas de animación ni se promete mejora de FPS.
2. En la nueva cola beta se reprodujo una NullPointerException cuando la consulta de
   transición cancelaba la petición. Se revalida cierre/petición después de esa consulta.
   La cola conserva una sola petición/frame, última interacción y cancelación por lifecycle.
3. El init-script de grafo también se ejecutaba en buildSrc: buscar el proyecto opcionalmente
   evita el error allí. La inspección Gradle real posterior pasó.

**6/6 pruebas beta pasan normal y `-O`**, con Java/Groovy/CMake reales, incluyendo
1000 interacciones sintéticas, reentrada, cancelación, configuración cerrada y comparación
byte a byte de políticas protegidas. Son seis métodos, no1000 pruebas ni mediciones Android.
Registro rojo previo conservado; ambas ejecuciones finales no tienen omisiones.

## Compilación y APK final

Compilación completa real ARM64, JNI y Chaquopy, sin SKIP: primer éxito401s.
Tras corregir la cola se recompiló incrementalmente: **BUILD SUCCESSFUL,74s**,
248 tareas (10 ejecutadas,238 up-to-date). El primer APK fue sustituido por el final;
ambos hashes se registran por separado. Se reutilizaron18 wheels, los cuatro ELF y
los tres wheels experimentales; no se reconstruyeron ni promovieron a dependencias activas.

- SHA256 final: `98de352740b07c3e6f00a2399246c9c60bc744ed44a976324c79e4132b086afd`.
- Tamaño: **116700247 bytes**. Versión13.0.2(1261), min24, target36, compile37.
- Sin certificado, firma JAR o bloque APK; zipalign16KB y CRC aprobados.
- 97 ELF totales:96 ARM64 aptos estáticamente para4KB/16KB; un payload debugpy no Android
  permanece visible. Cero DT_NEEDED ausentes, símbolos fuertes/versiones incompatibles.
- Cuatro ELF experimentales empaquetados exactos. Tres guardas nativas reducidas a RET;
  `.text` enlazada/paquetizada coincide,1833 comandos/1832 fuentes, targetandroid24.
- BuildConfig compilado: identidad propia,API0/hashvacío,push/configuraciones vacías,
  scope beta propio y seis capacidades false. DEX contiene entrada y cola beta.
- Manifiesto binario: sin INTERNET; solo ACCESS_NETWORK_STATE y permiso propio signature
  de receiver. Sin backup/restauración ni servicios/receivers externos activos;
  único launcher exportado dirige a BetaPreviewActivity no exportada. Provider de render
  jlatexmath interno habilitado; autoridades derivadas del applicationId.
- Grafo real:178 componentes compile/227 runtime, fachada beta propia.
- Escáner dirigido:14858 entradas/7 archivos anidados, cero claves cliente candidatas,
  claves retiradas, identidades/certificados ajenos o configuraciones de servicio embebidas.
  No equivale a demostrar ausencia universal de secretos.
- Prueba negativa Gradle Production: exit1, `FLEXYGRAM_PRODUCTION_INCOMPLETE`.

La APK Diagnostic anterior `29188186…` y los contratos v1/v2 no se sustituyen por esta APK.
No se afirma reproducibilidad byte a byte del APK completo ni identidad con binarios históricos.

## Conservación: bloqueo real pendiente

Respaldo local privado `FlexyGram-Beta-Offline-525b6999-Private.zip`,288410254 bytes,
SHA256 `9cad4dc2accdeb0fc6260ad889882b159fee11710f2c39213cae2c50a6ae8634`.
Incluye APK final, JNI sin stripping, comandos de compilación, insumos nativos recuperados,
logs y manifiesto de hashes;44 miembros,CRC y hashes individuales verificados.
No incluye clave de firma Android. Ningún binario se publica en GitHub.

**La conservación privada recuperable nueva NO está confirmada.** La vía autorizada de
subida falló con HTTP403 antes de iniciar la escritura. No se intentaron vías no autorizadas
ni se eludió el flujo de almacenamiento. El ZIP permanece en el workspace transitorio;
no debe confundirse con un respaldo entre sesiones. Hace falta restablecer la escritura
privada autorizada, guardar este ZIP y comprobar recuperación exacta antes de descartarlo.
El respaldo histórico de Diagnostic se recuperó y su hash exterior fue verificado;
no se sobrescribió ni se volvió a auditar innecesariamente.

## Android y siguiente puerta

No existe otro host de laboratorio autorizado accesible en esta sesión. Host actual:
sin KVM/TUN/contenedor utilizable, capacidades efectivas cero y seccomp; los fallos de
configuración de namespace offline ya conocidos no se repitieron. SDK/NDK se recuperaron
solo para compilar el cliente nuevo; no se descargaron de nuevo imágenes/emuladores.
No hubo boot, instalación, ejecución JNI/Python ni mediciones UI en Android.
No hay resultado TCG nuevo que presentar.

Orden concreto pendiente:
1. Conservar y recuperar el nuevo respaldo privado; revisar el delta PR23.
2. Host Linux dedicado sin dispositivos personales/USB, espacio suficiente en AVD,
   aislamiento offline demostrado; arrancar ARM64 API24/4KB y API35/16KB estrictas vacíos.
3. Contrato nuevo para esta identidad beta, separado de Diagnostic v1/v2; firma solo tras
   custodia recuperable y autorización independiente. No reutilizar firma de Production.
4. Instalación autorizada: JNI/Python,12 casos nativos por perfil y rutas UI sintéticas,
   lifecycle/pulsaciones rápidas/tema, Logcat sin datos privados y tráfico UID ausente.
5. Solo después de otra aprobación: perfil autenticable con identidad/credenciales propias,
   autorizaciones explícitas y pruebas correspondientes. Production sigue bloqueada.

Las evidencias adjuntas describen compilación/análisis host, nunca validación Android.
No se habilitan Actions, autenticación, servicios externos ni Paso4.
