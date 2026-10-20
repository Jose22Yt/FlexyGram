# P0.4c — ejecución de 304 regresiones y desbloqueo del laboratorio

FlexyGram 1.0, creado y dirigido por @Lukhou23. Base comprobada:
`a5459cf85c2c23e452bb09f38dfe0a28745ecda1`. Se conservan los cinco commits
posteriores a Work. PR17 permanece abierto, en borrador y sin fusionar.

## Resultados ejecutados

| Comprobación | Resultado real |
|---|---|
| Gate del HEAD solicitado, Python3.11.17 | **304/304 PASS** normal y `-O`, cero omisiones/errores/fallos |
| Preflight solicitado, por separado | **15/15 PASS** normal y `-O`; subconjunto del gate, no sumarlo de nuevo |
| Gate tras añadir infraestructura | **318/318 PASS** normal y `-O`; conserva las304 y añade14 regresiones |
| APK privada recuperada | SHA-256 `291881863ea81418fa6cb12104b6eaea4aee2403822894da2143a51f3030bdd5`,113080183 bytes |
| Revisor físico del candidato |97 ELF totales,96 ARM64; estado estático pendiente de Android |
| Respaldo privado | SHA-256 `c1c5caea6b949ea97ce4e912e17639c7d372aeb6def42a5c17909ebdfa963812`,58 hashes de miembros y CRC verificados |
| Borrador v2 recuperado/regenerado | Idénticos: `a4158e5e665deaaf91d8cad2e05d28715f2ef8465c3c2d635103c3220d280efe` |
| Arranque Android, instalación, firma | **No ejecutados** |

El primer intento de304 descubrió todos los casos y quedó BLOCKED (303 PASS,1error)
porque el fetch del commit base Git `ab063041…` todavía no había terminado. Se recuperó
ese objeto y se repitió la suite sin modificar ninguna prueba para ocultar el error.
Se conservan el intento inicial y las dos ejecuciones completas satisfactorias.
JDK21.0.10/JBR1163.105 y fuentes PR20/PR21 se recuperaron con los hashes fijados;
`pyelftools==0.33`. No se reconstruyeron APK, JNI, los cuatro ELF ni los tres wheels.
El código compilado de la APK sigue siendo `1177ceb8f4351b1626dd65e3dbd657f3b0ff159f`.

## Espacio e aislamiento: comprobación de alternativas reales

El mantenimiento automático eliminó el scratch anterior (SDK, imágenes y AVD incluidos).
Se recuperaron el repositorio y los dos respaldos privados de APK/borrador, sin publicar
binarios. Los archivos oficiales de imagen no aparecieron en la búsqueda de respaldos.
No se descargaron de nuevo varios GB mientras el aislamiento sigue bloqueado. Sus
pins, metadatos, recibos anteriores y recetas se conservan en Git; no se presentan las
verificaciones anteriores de imágenes como nuevas ejecuciones.

El nuevo filesystem de AVD dispone de **28263223296 bytes libres** en la comprobación
publicada, superior al umbral10737418240: **storage PASS**. Se resolvió así la falta de
espacio del entorno anterior; el valor pertenece a esta medición, no es una reserva.

| Alternativa comprobada | Resultado |
|---|---|
| `unshare --user --map-root-user --net true` | exit1, escritura de `/proc/self/uid_map` no permitida |
| `unshare --net true` | exit1, Operation not permitted |
| `unshare --user --net true` sin mapa UID | exit0: se puede crear el namespace, **no basta para aceptar el laboratorio** |
| Configurar/inspeccionar red con `ip` dentro de ese namespace | `Cannot open netlink socket: Operation not permitted`; no se obtiene el control offline requerido |
| `/dev/kvm`, `/dev/net/tun` | ausentes |
| Docker/Podman, sockets y Cuttlefish | no disponibles |
| Otro host Linux autorizado | no suministrado; no hay un conector apto de aprovisionamiento Android/Linux |

El proceso tiene CapEff/CapPrm0, NoNewPrivs1 y seccomp2. Se registraron las variantes
anteriores una vez; no se intentó eludir controles del host, elevar privilegios ni utilizar
un sandbox de medios/web como laboratorio. KVM ausente no prueba imposibilidad de TCG.
**No hay un error TCG observado**, porque no se arrancó Emulator sin aislamiento válido.

El preflight actual falla también por SDK/imágenes ausentes tras el mantenimiento.
Los dos perfiles están definidos y sus configuraciones históricas preservadas, pero sus
instancias AVD ya no existen aquí. Las invocaciones de la nueva herramienta para A y B
quedaron BLOCKED antes de crear un proceso Android. API, ABI y página reales del guest
siguen sin medir. La página4096 del host x86-64 no valida las bibliotecas ARM64.

## Cambio implementado: arranque vacío automatizado

`tests/native_compatibility/empty_avd_boot.py` prepara la etapa anterior a las pruebas
de aplicación. **No es otro ejecutor funcional**: reutiliza `run_lab.Adb` y
`run_lab.preflight`, y no modifica el runner histórico ni su contrato.

- Exige preflight sin bloqueos,10GiB libres y AVD nuevo ARM64 apuntando al directorio
  privado correcto; rechaza datos/snapshots anteriores, symlinks, rutas externas y claves INI duplicadas.
- Coteja los bytes de imágenes materializadas con el archivo oficial fijado, antes de boot.
- Crea un namespace user/net nuevo; comprueba identidad frente al padre, solo loopback
  activo y rutas sin gateway/default/uplinks antes de invocar Emulator o ADB.
- Elimina proxies/preloads/endpoints heredados, confina temporales, usa ADB local sin
  autoconexión mDNS y rechaza hosts con nodos USB expuestos para evitar teléfonos personales.
- Arranca un solo perfil vacío con TCG explícito, cámaras/audio desactivados, sin snapshots;
  acota tiempos, guarda salida real del emulador y detiene sus propios procesos al terminar.
- Reutiliza la validación ARM64/página/strict16K existente; además exige exactamente API24
  o API35, sin native bridge ejecutable, clientes preinstalados ni cuentas.
- Nunca llama `adb install`, firma APK ni inicia componentes de FlexyGram.

Las14 pruebas son sintéticas: namespace reutilizado/falsificado, uplink, gateway,
loopback inactivo, entorno heredado, AVD con datos/puntero externo, API incorrecta,
native bridge, cuentas/clientes, imagen modificada, INI duplicado y rechazo antes de
crear procesos. No constituyen boot real. El gate mínimo se eleva a318 (fixtures317/318).
El camino de boot satisfactorio todavía necesita ejecutarse en el host de laboratorio.

## Contrato v2 y siguiente puerta de ejecución

Se ejecutó `review_candidate_v2.py` contra la APK recuperada. El resultado privado es
idéntico al borrador conservado y sigue **no ejecutable**. Certificado, APK firmada y
runner firmado siguen null; custodia/activación/autorización siguen false. v1 conserva
SHA-256 `1a3ecb0160e2babf91c9ef7c1712c3577fadb73c5f647d17d84275af146dbb28`.
No se repinaron silenciosamente los adaptadores PR20/21 ni el verificador post-firma v1.
La diferencia histórica de `.text` de libtmessages sigue documentada: no hay bytes antiguos
para demostrar equivalencia completa ni atribuir todo a las447 rutas.

Para el siguiente trabajo hace falta un host/VM Linux de laboratorio sin USB passthrough,
con namespace offline **configurable y verificable**, al menos10GiB libres después de
materializar y un emulador capaz de arrancar esas imágenes ARM64. Primero ejecutar la
nueva herramienta sin APK, conservar errores TCG exactos si aparecen y medir API/ABI/página
y modo16KB. No sustituir por x86-64. Véase el procedimiento externo actualizado.

Después: aceptación del candidato, custodia privada recuperable y autorización independiente
de clave/firma/instalación; adaptación v2 separada y revisada de post-sign/runner/adaptadores;
12 casos reales por perfil, restauración sintética, permisos/componentes, logs y tráfico UID.
Eso valida Diagnostic offline; una beta autenticable todavía exige sus configuraciones
propias y otra aprobación de implementación. Ningún resultado host habilita Production.

Main/develop intactas, PR2 abierto. Sin claves, firma, APK instalada/distribuida,
autenticación, servicios externos, Actions habilitado o Paso4.

[Recibos y logs](evidence-lab-execution-20261020/) ·
[Procedimiento](LAB-V2-EXTERNAL-PROCEDURE.md) ·
[Investigación JNI conservada](JNI-LAB-V2-REVIEW-2026-10-20.md).
