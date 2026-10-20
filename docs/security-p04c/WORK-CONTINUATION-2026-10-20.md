# P0.4c — continuación ejecutada en Work (UTC 2026-10-20)

FlexyGram, @Lukhou23. Base comprobada:
`c8b5f63f34ea06c9fcdc40a9f37c55661f189190`, PR17 borrador hacia develop.
Encargo: comentario6280842488. No se fusiona, firma, instala o distribuye.

## Ejecución de pruebas y corrección mínima

Python3.11.17 y pyelftools0.33 del lock. Checkout íntegro y16 submódulos fijados.
La primera ejecución descubrió228 casos:211 aprobados,17 errores de entorno,
0 fallos de aserción y0 omisiones. Se recuperaron JBR21.0.10 y los archivos auxiliares
PR20/21 por commit y SHA fijados; no se modificaron sus implementaciones.

**228/228 PASS** normal y `-O`, cero fallos/errores/omisiones.
Se corrigió una limitación de diagnóstico real: el verificador de APK devolvía solo
ValueError/BLOCKED al faltar el binario. Ahora mantiene status BLOCKED/exit1 y añade
`blocker=BLOCKED_MISSING_PRIVATE_APK`; corrupción y enlaces inseguros se distinguen
como VERIFICATION_FAILED. No imprime rutas privadas ni rebaja ninguna comprobación.
Tres regresiones sintéticas adicionales: ausencia, enlace colgante y bytes corruptos.
**231/231 PASS** normal y `-O`, cero fallos/errores/omisiones; umbral228 intacto.

El total único de esta continuación es231; las modalidades y suites seleccionadas
no se suman de nuevo. Incluye reconstrucción/reproducibilidad, revisión de evidencias,
APK sintética, contrato v2 y14 casos post-firma sintéticos. No se ejecutó el CLI
post-firma contra ninguna APK real. Las102 regresiones ajenas al gate son evidencia
histórica, no se anuncian como reejecutadas ahora.

```sh
JAVA_HOME="$JDK21" FLEXYGRAM_TEST_PR20="$PR20_PINNED" FLEXYGRAM_TEST_PR21="$PR21_PINNED" python3.11 -B tests/native_compatibility/run_gate.py --output /private/native-final.json
JAVA_HOME="$JDK21" FLEXYGRAM_TEST_PR20="$PR20_PINNED" FLEXYGRAM_TEST_PR21="$PR21_PINNED" python3.11 -B -O tests/native_compatibility/run_gate.py --output /private/native-final-opt.json
python3.11 -B tests/native_compatibility/review_unsigned_contract.py
python3.11 -B tests/native_compatibility/create_lab_v2_draft.py --output /private/lab-v2-proposed.json
python3.11 -B tests/native_compatibility/verify_private_unsigned_apk.py --apk "$ORIGINAL_PRIVATE_APK"
```

La revisión verifica44 evidencias históricas. El borrador v2 se escribió fuera del
checkout con permisos0600 y estado BLOCKED_UNSIGNED_V2_DRAFT_NOT_LAB_CONTRACT.
No activa un contrato runtime, custodia, firma o aprobación. V1 permanece inalterado.

## Artefactos recuperados y APK original ausente

Los respaldos privados originales y reconstruidos se recuperaron y verificaron
contra sus SHA256 completos.25 miembros originales exactos;18 wheels experimentales
verificados; los cuatro ELF recuperados pasan de nuevo la comparación ABI con sus
originales. No se repitió la reconstrucción nativa A/B ni se cambiaron sus hashes.

**La APK ddb7b017… no se recuperó.** El workspace anterior ya no está disponible;
la búsqueda por nombre exacto y el listado completo de APK persistidas no la encuentran.
Sí existen APK antiguas distintas, que no se descargaron/usaron como sustitutos.
Los respaldos conservados contienen inputs/wheels, no la APK. El verificador físico
devuelve BLOCKED_MISSING_PRIVATE_APK; revisar44 archivos no equivale a comprobar bytes.

Se prepara una reconstrucción **solo del cliente unsigned**, reutilizando el overlay18
wheels ya reconstruido, en un worktree independiente del commitc8b5f63. Todos los
archivos Android activos son idénticos a723580b5. JNI y Chaquopy se compilan completos;
ninguna clave se carga o genera. Si el SHA cambia se registrará como candidato nuevo,
sin sustituir el pin ddb7b017… ni las evidencias históricas. Build todavía en curso en
este checkpoint: no se declara éxito o equivalencia del nuevo APK.

## Laboratorios preparados, sin boot ni instalación

Descargados desde Google y comprobados con checksums oficiales fijados, CRC y SHA256
registrado: ADB37.0.1, Emulator37.2.12, SDK37r02, BuildTools36.0.0,
imagen AOSP ARM64 API24r09 y Google APIs ps16k ARM64 API35r05.
JDK21, Gradle9.7.1, NDK27.2.12479018 y CMake3.31.6 recuperados sin sustituir versiones.

Dos AVD configurados y reconocidos por `emulator -list-avds`. Launcher headless y
motor QEMU ARM64 responden a versión. No se declara que el motor pueda arrancar estas
imágenes en este host. Sin KVM; `accel-check` devuelve3. El intento de crear un
namespace de red aislado falla con Operation not permitted. No se arrancan invitados
con aislamiento no probado. No usar -net none como sustituto no verificado de un
cortafuegos/namespace. El host no proporciona las capacidades de red requeridas.

Se recuperaron3.05GB de asignación física mediante huecos en imágenes: hashes antes
y después idénticos. No se alteraron bytes de imagen para conseguir compatibilidad.
El runner existente de12 casos se recompiló con SDK37/min24 **unsigned y sin permisos**;
no se firmó/instaló y mantiene el contrato histórico, no el borrador v2.

Pendientes por perfil: boot ARM64 real, API/ABI/PAGE_SIZE medidos;16KB estricto y
compatibilidad retroactiva desactivada comprobada, root/AOSP y aislamiento de red
verificable; arranque del cliente, JNI/Python y12/12 casos, logs/counters/mappings.
La disponibilidad de una imagen ps16k no acredita PAGE_SIZE=16384 ni compat desactivada.

## Custodia y autorizaciones

No hay un vault de firma autorizado conectado ni una clave pública de cifrado del
custodio con fingerprint verificado. No se buscan claves privadas locales ni se
genera otra identidad para aparentar continuidad. El dueño debe escoger/proporcionar
ese recurso. La opción GPG requiere primero cifrar/recuperar un reto sin secretos,
verificar destinatario/fingerprint y después recuperación del respaldo sellado.
Un JSON que diga custody=true no sustituye la prueba ni revisión humana.

La generación condicionada sigue bloqueada hasta custodia recuperable probada.
**La firma de APK requiere autorización separada, todavía ausente.** No pedir
contraseñas, claves privadas, API Hash o códigos de Telegram. El plan detallado
existente en signing-v2/PLAN.md se conserva y no se ejecuta.

Evidencias de esta ejecución: `evidence-work-20261020/`. No se modificaron Production,
main/develop, políticas, interfaz, animaciones, navegación o dependencias activas.
Sin Actions, cuentas, autenticación, proveedores, instalación, distribución o Paso4.
