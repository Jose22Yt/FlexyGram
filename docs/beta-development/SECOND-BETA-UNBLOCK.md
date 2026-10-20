# Work2 — integración27/26 y recuperación de insumos

FlexyGram1.0, creado y dirigido por @Lukhou23. Continuación de PR23
`44a607d330f529c8137638b9107e0b9a3aace837`, sin modificar ramas de Work1.
Este informe sustituye las dependencias operativas antiguas de
SECOND-BETA-PREPARATION.md: **no se espera una certificación de la APK antigua**.

## Código incorporado

- `8e43f8da6665d4d4187f61c1b0b7331541cec884`: los dos archivos de PR27
  `406ba91f303d8469981c74fba962acb0e7498add`, byte por byte. Integra la corrección Java
  `c0e752cd0c11ade560140fafdb65d9affad04689` y su regresión posterior. Una rapid_tap
  deja de tener una presentación instantánea ficticia: comparte aceptación y endpoint
  observable de la navegación; cancelación, abandono y timeout siguen ese recorrido.
  transition_interrupt termina en cancelled para medir cancelación de una intención
  pendiente; no afirma cancelar un Animator nativo activo. No cambia duraciones.
- `5f5cadc38978552577113a6dad0f52e286fe3e06`: exactamente los siete archivos nuevos
  del delta PR26 `2363f38… → 51f60082d81269a9010baa92415cfb9f3001f4a0`.
  Incorpora los12 casos personales, importador y11 regresiones. No vuelve a integrar
  PR25 ni modifica los analizadores de PR24. Los informes copiados de PR26 conservan
  su procedencia histórica; las ejecuciones nuevas están en evidence-unblock-second-beta.
- Se añade una regresión puente: productor/cola/exportador Java reales generan dos
  lotes privados sintéticos; el importador real de PR26 los ordena, concatena y comprueba
  chat_open/chat_close/rapid_tap sin pérdidas ni endpoints inventados. No es Android.

NotificationCenter y ActionBarLayout permanecen idénticos al HEAD44a607; sus regresiones
siguen pasando. No se duplica el arreglo anterior ni se modifican animaciones, permisos,
JNI, políticas Diagnostic/Production, autenticación, dependencias activas o contratos.

## Pruebas reales

**60 métodos distintos PASS en Python3.11.17 normal y -O**, cero omisiones:
28 cliente (27 tras integrar PR27 +1 puente),11 importador y21 handoff. Java21,
Groovy/Gradle y CMake se ejecutan realmente en host; Activity/Android/Chaquopy de las
regresiones usan dobles explícitos. No sumar los modos como120 pruebas distintas.
Se conservan IDs, hashes y los seis logs en [results.json](evidence-unblock-second-beta/results.json).

Fallos iniciales del arnés por variables ausentes (FLEXYGRAM_DIAGNOSTICS_SOURCE,
FLEXYGRAM_CMAKE y FLEXYGRAM_GRADLE_HOME) se resolvieron aportando las herramientas
fijadas, sin cambiar verificaciones. No se atribuyen esos fallos a defectos del cliente.

Reproducción desde este checkout, con fuentes PR24 fijadas read-only y herramientas
verificadas ya presentes en las rutas privadas del operador:

```sh
export JAVA_HOME="$BETA_JDK21"
export FLEXYGRAM_CMAKE="$BETA_CMAKE_3316"
export FLEXYGRAM_GRADLE_HOME="$BETA_GRADLE_971"
export FLEXYGRAM_DIAGNOSTICS_SOURCE="$BETA_PR24_PINNED"
for suite in beta_development personal_beta beta_handoff; do
  "$BETA_PYTHON311" -B -m unittest discover -s "tests/$suite" -v || exit 1
  "$BETA_PYTHON311" -O -B -m unittest discover -s "tests/$suite" -v || exit 1
done
```

El importador comprueba hashes de analyze.py/capture.py del PR24 `db5b9a1…`
antes de ejecutarlos. No se crean otro collector ni un segundo ejecutor Android.

## Insumos recuperados, no reconstruidos

La beta histórica `98de352740b07c3e6f00a2399246c9c60bc744ed44a976324c79e4132b086afd`
queda **no recuperada en los entornos actuales**. Esto no demuestra pérdida definitiva.
No se reemplaza ese hash ni se atribuye a una compilación nueva.

Sí se recuperó íntegramente un respaldo privado histórico **Diagnostic**, distinto de
esa beta:302608432bytes, SHA256`c1c5caea6b949ea97ce4e912e17639c7d372aeb6def42a5c17909ebdfa963812`.
CRC ZIP verificado. Del archivo interno nativo61MB
`979c5c5f61519949dd677a6d4892fbd13e202af803b291b0b7003b4c5bd2ecb2` se recuperaron:

- 18 wheels originales, comprobados individualmente contra wheels.lock.json activo.
- 18 wheels del overlay experimental, incluidos los3 reconstruidos históricos, comprobados
 con experimental_wheels.py y su manifiesto aprobado.
- 4 ELF reconstruidos históricos:libfreetype/libxml2/libxslt/libexslt. Hashes exactos y
 condiciones PT_LOAD4KB/16KB comprobados con llvm-readelf de NDK27c. No se reconstruyen.
- Fuentes, recetas y manifiestos históricos; sin sobrescribir sus contratos.

El respaldo Diagnostic contiene otro APK; no equivale a recuperar la beta98de… ni acredita
el código actual. No se publican APK, wheels, fuentes binarias ni claves en GitHub.

Se restauraron JDK21.0.10, Gradle9.7.1, NDK27.2.12479018, SDK35/37 y BuildTools36,
verificando los hashes fijados. CMake3.31.6, Ninja1.12.1 y Python3.11.17 funcionan.
Los16 submódulos raíz se recuperaron en sus commits fijados. Se reparó la extracción local
para conservar los35 enlaces simbólicos originales del ZIP NDK; no se cambió el NDK.
No se descargaron imágenes ni se repitieron intentos de aislamiento/emuladores.

## Estado exacto de compilación

Se preparó un checkout hermano aislado del código `5f5cadc…`, con el overlay aprobado,
una **copia nueva** del manifiesto y `prepare_experiment.py --unsigned`. Los locks y
build.gradle activos no cambian. No se accede a claves de firma.

Se ejecutó sólo `:TMessagesProj:assembleBetaDevelopmentDebug --dry-run` con el opt-in
beta y ARM64, **sin ejecutar compilación JNI, Chaquopy o empaquetado**. La configuración
falla en settings.gradle:15 al resolver Foojay1.0.0. La ejecución `--info` muestra
`java.net.SocketException: Network is unreachable` hacia el proxy configurado para
Maven. Curl al POM oficial devuelve200; la conectividad TCP Java al proxy funciona.
La selección IPv4 tampoco resuelve el fallo Gradle. No se conoce aún la causa completa
entre esos transportes; no se elimina Foojay ni se cambian versiones/repositorios.
No se presenta esta ejecución fallida como BUILD SUCCESSFUL o resolución completa.

Conservar el fallo en [recibo](evidence-unblock-second-beta/next-beta-gradle-dry-run.json)
y [log saneado](evidence-unblock-second-beta/next-beta-gradle-dry-run.log).
El comando real y gate integrado siguen documentados en SECOND-BETA-PREPARATION.md,
pero aún no están ejecutados sobre este código. No hay APK nuevo ni hash nuevo.

## Conservación y siguiente bloqueo

La lectura/recuperación del respaldo privado sí funcionó. La prueba nueva de escritura
usó57671850bytes sintéticos sin APK/secretos y falló HTTP403 **antes de transferencia**;
no se cambió de endpoint ni se eludió ese error.

El responsable conectó Dropbox: se verificó instalado/habilitado. Sin embargo, esta
sesión no expone ninguna operación Dropbox de subida/descarga, ni un recurso de skill
que la proporcione. **No se ha ejecutado una prueba de escritura o recuperación en
Dropbox.** Conexión habilitada no demuestra permiso de escritura ni custodia recuperable.
Hace falta disponer de esas operaciones en la sesión, no volver a solicitar conectar una
cuenta ya conectada ni compartir contraseñas/tokens. No se sube nada mediante APIs no
anunciadas y no se genera una APK mientras falte la prueba privada de recuperación.

No existe ya dependencia de Work1 para certificar el archivo antiguo. Orden pendiente:

1. Exponer operaciones del Dropbox conectado; guardar y recuperar un ZIP sintético
   privado con SHA exacto, sin enlace público ni sobrescritura. Verificar capacidad para
   un respaldo de APK/clases/JNI/logs, no sólo metadatos.
2. Resolver el transporte de dependencias Gradle fijadas y pasar configuración; no
   convertir fallos de red en cambios de versiones o controles debilitados.
3. Con almacenamiento verificado, la compilación unsigned nueva ya está autorizada:
   build ARM64 real JNI/Chaquopy, gate APK/manifiesto/DEX/ELF4KB/16KB y verificación de
   copia privada recuperada. Hash nuevo, sin modificar hashes históricos.
4. Sólo después: custodia de clave y autorizaciones independientes para generación,
   firma, entrega privada, instalación y ejecución personal offline. Esta continuación
   no las concede. Work1 conserva responsabilidad de esa preparación física.

No se declara resuelto el arranque: todavía no hay una ejecución Android del cliente.
Siguen pendientes carga real JNI/Python, UI sintética, restauración/lifecycle y páginas
reales de memoria. Las pruebas host no miden latencia/FPS ni certifican16KB en Android.
Main/develop y ramas de Work1 intactas; PR23 continúa en borrador, sin fusiones,
Production, autenticación, servicios externos, Actions ni Paso4.
