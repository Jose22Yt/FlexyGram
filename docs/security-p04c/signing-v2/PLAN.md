# Firma laboratorio v2 y adaptación de evidencias

FlexyGram, creado y dirigido por @Lukhou23. Base revisada:
`25919fc3d4115e7d0ea4260af2db006a302f4f7d`, PR17 borrador hacia develop.
Procedimiento **FG-LAB-SIGNING-2.0-PROPOSED**. No se firma ni distribuye APK.

## Resultado de la autorización de generación

El propietario autorizó expresamente generar una clave **solo Diagnostic/laboratorio**,
y exigió detener la generación si no pudiera protegerse y conservarse con seguridad.
La autorización es válida; **no hace falta pedirla de nuevo**. El recurso que falta es
un canal de custodia recuperable de secretos o un destinatario de cifrado controlado
por el propietario. No se ha generado clave, contraseña, certificado o almacén nuevo.

El entorno ofrece JDK21/keytool y GPG, pero no un gestor de secretos conectado,
keyring de escritorio configurado ni destinatario público/fingerprint designado por
el propietario. Un ZIP privado de fuentes no equivale a una bóveda de contraseñas.
El workspace temporal puede ser retirado por mantenimiento: no es custodia durable.
Crear un PKCS12 cifrado y perder su contraseña no resolvería el problema; guardar el
password en claro junto al PKCS12 en archivos ordinarios tampoco proporciona la
protección requerida. No se presupone que un directorio local sea almacenamiento cifrado.

**Estado BLOCKED_CUSTODY_NOT_CREATED.** identity.pending.json reserva un identificador
propuesto, sin presentarlo como clave existente. Fecha y SHA256 nuevos son null, no
valores ficticios. El certificado27ef63ae… y APK17c32ab3… siguen como referencias
históricas, con sus evidencias intactas. No se deriva una clave privada de un certificado.

### Recurso concreto para desbloquear

Se necesita una de estas opciones, siempre en almacenamiento privado autorizado:

1. Un gestor de secretos que permita guardar y recuperar el almacén y sus contraseñas
   con controles de acceso/retención, explícitamente conectado para este proyecto; o
2. **Una clave pública de cifrado del custodio y su fingerprint verificado** (p. ej. GPG),
   cuya clave privada permanezca con él, para sellar conjuntamente keystore+contraseña.
   El propietario debe poder probar la recuperación. La clave pública no es una contraseña
   ni permite firmar APK; no se pide compartir ninguna clave privada o secreto por chat.

No se seleccionó una identidad GPG arbitraria del host ni se creó una segunda clave de
cifrado con el mismo problema de custodia. El respaldo solo cifrado podría guardarse
privadamente después; nunca se pondría su contenido descifrado en GitHub. La copia de
insumos originales previamente conservada sigue disponible, sin secretos.

## Secuencia propuesta de generación y custodia — no ejecutada

1. Verificar destinatario/custodio y recuperación de una prueba **sin secretos** antes
   de generar material de firma; o verificar lectura/escritura del vault autorizado.
2. Reservar directorio privado nuevo0700 fuera de Git. Crear contraseña CSPRNG de al
   menos32 bytes en memoria; no imprimirla, pasarla por argumentos, escribirla en logs,
   local.properties, historial de shell ni documentación. Utilizar transporte de secretos
   del almacén o `keytool -storepass:env/-keypass:env` con entorno temporal privado,
   teniendo en cuenta acceso del mismo usuario/administrador a procesos. No afirmar
   aislamiento frente a un administrador host no confiable.
3. Generar exclusivamente PKCS12 Diagnostic, alias `flexygram-diagnostic`, RSA3072,
   certificado SHA256withRSA, validez prevista10 años; comprobar los parámetros de
   cifrado y KDF del almacén de JDK21. Permisos0600; no debug.keystore estándar,
   Production ni fallback. No usar un archivo o alias anterior sin comprobarlo.
4. Exportar únicamente certificado DER público; comprobar clave privada/certificado en
   memoria/host confiable y registrar SHA256 DER, algoritmo real, identificador, fecha
   real y procedimiento. No confundir algoritmo del certificado con los esquemas v2/v3
   de firma APK, que se comprobarán posteriormente con apksigner.
5. Sellar la copia de seguridad, incluyendo contraseña, al destinatario público verificado
   o guardar ambos mediante el vault con sus controles. Conservarla solo en destino
   privado autorizado. No guardar password en claro al lado de un PKCS12 cifrado.
   Verificar persistencia y que el custodio puede restaurar el material y obtener el
   mismo certificado, sin utilizar APK. Una prueba de recuperación no permite publicar
   la clave ni el secreto recuperado.
6. Eliminar los temporales en claro según el entorno; no prometer borrado físico seguro
   de capas/SSD que no se controla. Confirmar custodia antes de depender de esa identidad.
7. Publicar **solo metadatos públicos**. Detenerse: esta autorización de generación no
   autoriza usar la clave para firmar una APK. El plan y el nuevo contrato deben revisarse
   antes de cualquier build firmado, resignado o distribuido.

El keystore PKCS12 ya incorpora protección por contraseña, pero su seguridad y
recuperación dependen del custodio y respaldo anteriores. Hasta resolverlos no se
inicia el paso2. Esta propuesta no se ejecuta automáticamente al importar ningún test.

## Reconstrucción experimental y firma posterior propuesta

Se comprobaron nuevamente las huellas de los18 originales ARM64 y las fuentes
recuperadas.15 originales coinciden con el overlay; los otros3 son insumos, **no** los
wheels reconstruidos. La copia privada de recuperación y los archivos activos no cambian.
Los12 casos funcionales,207 regresiones y evidencias96/96 anteriores se conservan.

Después de cerrar custodia, y antes de firmar APK, presentar para revisión:

1. Entorno fijado existente: Python3.11/pyelftools0.33,JDK21,Gradle9.7.1,AGP9.3.1,
   SDK37/BuildTools36.0.0,NDK27.2.12479018,CMake3.31.6,Chaquopy17 y submódulos.
   No actualizar masivamente SDK/NDK/Python/Gradle ni minSdk/target.
2. Reutilizar rebuild_candidates.py y experiment_recipe.py/GNUld2.42 en dos destinos
   nuevos para obtener los4 ELF; conservar features,ABI/DT_NEEDED/versiones, licencias
   y la finalización GNU revisada. experimental_wheels.py debe reconstruir3 wheels y
   conservar15 originales. Comparar cada SHA y contenido con los aprobados: cualquier
   discrepancia se investiga, no se oculta actualizando hashes.
3. Preparar overlay únicamente en worktree desechable. No modificar los locks/pip,
   políticas Java/JNI, servicios o capacidades activas de Diagnostic. Inspección estática
   completa de los96 ARM64,API24,16KB,dependencias/imports y manifiesto/DEX/recursos.
4. Crear **contrato experimental v2 separado** cuando existan datos medidos: referencia
   al histórico, nuevo certificado real, nueva APK/hash y recibos de firma; mantener los
   hashes ELF/wheels/casos originales si efectivamente coinciden. Los campos pendientes
   son bloqueo. No borrar el contrato v1 ni fabricar hashes antes del build.
5. Solo tras aprobación expresa del plan de firma: firmar Diagnostic y test APK con la
   misma clave de laboratorio, configurar secretos privadamente, verificar certificado
   y esquema APKv2. No producir Production ni distribuir APK. La compilación firmada
   no se ha realizado en esta etapa.
6. Aceptar que la nueva firma **no actualiza directamente** una instalación anterior.
   Android tampoco permite que un test APK con nueva firma instrumente el target
   antiguo sin compatibilidad de certificados. Usar emuladores con userdata totalmente
   nuevo; no desinstalar apps personales ni migrar/restaurar sesiones para sortearlo.
   El SHA de APK firmada cambia; ni siquiera con la misma clave se promete determinismo
   de todo el ZIP sin comprobar timestamps/inputs/build. Mantener trazabilidad por capas.
7. Probar A:ARM64/API24/4096 y B:ARM64/página real16384 estricta, offline,sin cuentas.
   Solo el runner existente instala/ejecuta. Los12 casos por laboratorio,JNI/Python,
   mappings/logs/counters y validación conjunta siguen pendientes. No atribuirlas al build.

## PR20 corregido y PR21

PR20 conserva `3aaae0fc3065b631968476195da5adfd13ba95d8`.
Sus **29 pruebas pasan con Python3.11.17 normal y -O**, sin fallos/omisiones.
Se revisaron comprobación de uname,ABI primaria,native bridge y bloqueo por indicadores
críticos de logs. Se mantiene readonly y no es autorización de instalación por exit0.
Las diferencias restantes —Cuttlefish local/modo16KB estricto/contrato único— continúan
cubiertas por PR17 y su adaptación, no se debilitan para forzar equivalencia.

PR21 conserva `88f988ee844248a4513281cfe7818777fbda660e`,24 pruebas reejecutadas
normal y-O. Su contrato histórico todavía fija certificado y APK antiguos. El nuevo
certificado **no puede introducirse mediante un argumento o fallback**: requiere una
nueva versión revisada también de ese validador y del adaptador.

### Adaptación implementada, sin otro ejecutor Android

`tests/native_compatibility/android_lab/pr21_adapter.py` opera **solo sobre archivos**.
No genera claves, firma, llama ADB, abre red ni inicia procesos Android. Exige código
PR20/21 exacto por SHA256 antes de importar sus módulos; no copia sus implementaciones
ni los integra en la APK normal. Reutiliza matrix de PR17, read_log_counts de PR20 y
validate de PR21. Los commits y hashes auxiliares están fijados en PINS.

Antes de exportar requiere ambas evidencias completas: JSON sin claves duplicadas/
no finitos,huellas de archivos,nonce/perfil,instalación exitosa,cold-start,evidencias de
paquete sin INTERNET,recibo de runner firmado/fuentes coincidentes,imagen,inputs18wheels/
3rebuilt/4ELF,capacidades y los12 casos. Relee counters reales IPv4/IPv6 y compara
con el JSON, rechazando bool como cero; analiza categorías Python/OOM/crash/linker y
errores Java. Cualquier dato ausente,contradicción,case omitido o cambio de contrato bloquea.

Genera en directorio privado nuevo, con archivos0600:

- evidence-pr21.json: resumen derivado en el formato **histórico** exacto PR21.
- provenance.json: nonces,huellas de resultados/logs/imagen/runner/contrato,versiones
  auxiliares y hash del resumen. `runtime_certified=false`,sin distribución/fusión.

El exportador no prueba que ocurriera una ejecución: los reportes pueden falsificarse
por un operador; conserva la necesidad de revisar evidencias primarias. No convierte
fixture sintético en certificado Android. El origen primario nunca se sustituye por
el resumen. Está probado con fixtures; todavía no existen resultados Android reales.

```sh
# Sobre dos runs reales completos; no crea observaciones faltantes.
python3.11 tests/native_compatibility/android_lab/pr21_adapter.py \
  /private/runs/api24/result.json /private/runs/16k/result.json \
  --pr20-preflight /private/checkouts/pr20/tools/android_lab_preflight/preflight.py \
  --pr21-validator /private/checkouts/pr21/tools/android_lab_evidence/check.py \
  --output /private/results/export-new
```

16 regresiones nuevas, normales y-O: positivo sintético,no certificación,código auxiliar
alterado,JSON duplicado/no finito,formato incompatible,perfil repetido,proveniencia o
instalación ausentes,errores Python/OOM,counters contradictorios/bool,runner alterado,
entorno diferente,cold-start incompleto,case omitido,contrato cambiado y CLI sin archivos.
También se reejecutaron32 pruebas del runner anterior normal/-O. Total de esta etapa:
**101 pruebas únicas** (29+24+32+16),repetidas con-O sin doble cómputo. No se reejecutó
la suite completa de207 anteriores; permanece intacta y se agregan16 regresiones.
Las pruebas del adaptador requieren las rutas de fuentes PR20/21 fijadas, sin descargarlas
ni omitir tests por su ausencia:

```sh
FLEXYGRAM_TEST_PR20=/private/checkouts/pr20/tools/android_lab_preflight/preflight.py \
FLEXYGRAM_TEST_PR21=/private/checkouts/pr21/tools/android_lab_evidence/check.py \
python3.11 -m unittest discover -s tests/native_compatibility -p test_pr21_adapter.py -v
```

Main/develop intactas; PR17 y auxiliares abiertos/sin fusión; PR2 abierto. Sin firma de APK,
clave creada,secretos publicados,Actions habilitado,servicios,autenticación,Production,
UI/animaciones,rendimiento o Paso4. Se detiene antes de generar la clave hasta disponer
**del recurso de custodia**, no por falta de autorización del propietario.
