# P0.4c — revisión del JNI y preparación real del laboratorio v2

FlexyGram, creado y dirigido por @Lukhou23. Ejecución del 20 de octubre de 2026 UTC
(19 de octubre en Bogotá). Base verificada: `9786b201e059f9093718dd828bd6bdd354ed8c08`.
Se conservaron los 16 commits concurrentes hasta `c369e4ea13862430c147e39ce3f5913a44e05d85`,
que será el padre de esta continuación. PR #17 en borrador, sin fusionar. Cambios de esta continuación: pruebas host,
analizadores y documentación; ningún archivo Android, Gradle, JNI del cliente o wheel activo cambia.

## Candidato conservado, sin nueva compilación de APK

Se recuperó la copia privada y se verificaron SHA-256/CRC del respaldo y sus **58 miembros**.
La APK conserva **113080183 bytes** y SHA-256
`291881863ea81418fa6cb12104b6eaea4aee2403822894da2143a51f3030bdd5`.
Su código compilado sigue siendo `1177ceb8f4351b1626dd65e3dbd657f3b0ff159f`.
No se ejecutó Gradle ni se reconstruyeron los cuatro ELF/tres wheels experimentales.
El respaldo privado original y su copia persistente permanecen conservados;
se retiró únicamente una copia local duplicada tras verificar igualdad de hash para liberar espacio.

## Investigación de libtmessages.49.so

| Evidencia real | Resultado |
|---|---|
| JNI empaquetado | `756e53d23f29ecca32d7c9706375494cdf2217d0db8d314a4195d0174400912b` |
| JNI histórico registrado | `b52a40892f7b69162be55cdcced8d3c143cbf85c10243aea0abfbe5f05f89cff` |
| Binario histórico disponible | **No**; solo hashes/metadatos publicados |
| Comparación actual enlazado vs empaquetado | Todas las secciones SHF_ALLOC, sus bytes/layout, ABI ELF, punto de entrada y program headers iguales |
| Símbolos dinámicos definidos global/weak | **385**, iguales en ambas copias actuales; tipado, binding, visibilidad, direcciones y tamaños cotejados |
| Relocaciones decodificadas | **58076**, registros iguales; se conserva inventario y hashes de las secciones de relocación |
| Dependencias | 10 bibliotecas de Android; DT_NEEDED y SONAME iguales a los registros históricos; sin RPATH/RUNPATH |
| Stripping | Retira nueve secciones de depuración/símbolos no cargables, sin modificar secciones cargables |
| Tres guardas nativas | `ConnectionsManager::init`, `ConnectionSocket::openConnection` y `openConnectionInternal`: solo `RET`; `.text` empaquetada coincide con el enlazado |
| Enlace repetido real | Se reutilizaron los objetos existentes: 15,16 s, ELF sin stripping idéntico; tras strip, mismo SHA-256 que el JNI de la APK |

El segundo enlace escribió exclusivamente una salida privada, sin recompilar fuentes ni
sobrescribir la biblioteca original o la APK. El objeto enlazado original y su respaldo
siguen disponibles. Repetir ese enlace tras perder el árbol de objetos requeriría recuperarlo
o recompilarlo; el respaldo no pretende contener todos los objetos intermedios.

### Las 447 rutas no son solamente información de depuración

Las **447 coincidencias están en `.rodata`, SHF_ALLOC**, ninguna en una sección ejecutable.
Por tanto, sobreviven al stripping y forman parte de los datos cargados del cliente.
Son rutas de compilación, no credenciales; no se encontraron RPATH/RUNPATH que las utilicen
como directorios de búsqueda de bibliotecas. Normalizarlas podría mejorar reproducibilidad
y evitar divulgar rutas del build, pero no se aplicó ningún cambio al cliente.

El hash histórico registrado de `.text` es
`44a7127ecacd421cec0d9aac758fc439a13c0aab070f82e517b39b2793350ed7`;
el actual, `aa570dbb8589d03ddda14f2358c560a96a06b5f98ced2ea80bf7a70bf738654a`.
**Los bytes de código también difieren según esos registros. No basta hablar de DWARF o strings.**
Sin los bytes antiguos no es posible desensamblar/comparar sus instrucciones, relocaciones,
secciones de datos o ABI exportada completa, ni determinar la causa de cada diferencia.
La igualdad de dependencias y hashes de otros ELF no sustituye esa comparación.

### Experimento controlado ARM64, fuera de la aplicación

Se ejecutó dos veces un experimento de cuatro ELF diminutos por ejecución, con NDK27.2,
API24, mismo C y prefijos de ruta diferentes. El fixture utiliza `__FILE__` y
`sizeof(__FILE__)` explícitamente: es una demostración causal sintética, no una reproducción
de funciones del cliente. Cambiaron bytes de `.text`, datos y relocaciones; con
`-ffile-prefix-map` hacia una raíz canónica los dos resultados fueron idénticos.
El analizador separa diferencias de **bytes** y de **direcciones/layout**.
Esto demuestra un mecanismo posible, **no que todas las diferencias históricas del JNI
se deban a él**. No se parchearon binarios ni se alteraron hashes/contratos históricos.

[Resumen JNI](evidence-jni-lab-v2-20261020/jni-deep-summary.json) ·
[Secciones y comparación](evidence-jni-lab-v2-20261020/elf-sections-comparison.json) ·
[Símbolos](evidence-jni-lab-v2-20261020/jni-dynamic-symbols.json) ·
[Reenlace](evidence-jni-lab-v2-20261020/relink-determinism.json) ·
[Experimento](evidence-jni-lab-v2-20261020/path-prefix-experiment-portable.json).

## Pruebas y herramientas nuevas

**300/300 PASS** en Python3.11 normal y `-O`: las 231 anteriores, 27 incorporadas por el propietario, 39 de esta continuación y tres regresiones del inventario bootstrap.
Cero fallos, errores u omisiones. Se elevó el mínimo del gate a300 y sus fixtures a299/300;
no se amplió la lista de cambios permitidos ni se suavizaron controles anteriores.

- `elf_candidate_review.py`: compara bytes/layout cargables, ABI, símbolos, relocaciones,
  dependencias y rutas sin cargar el ELF. Sus mutaciones sintéticas detectan cambios reales.
- `review_candidate_v2.py`: reutiliza el verificador físico `review_rebuilt_candidate.py`
  incorporado por el propietario; produce únicamente un borrador v2 privado no ejecutable.
  Conserva los pins v1 y del inventario de wheels. No duplica el verificador de bytes.
- `lab_host_preflight.py`: comprueba imágenes fijadas, API/ARM64, kernel gzip o plano,
  herramientas e infraestructura. No llama ADB contra dispositivos ni arranca Android.
- `materialize_lab_images.py`: materializa imágenes oficiales de forma dispersa, valida rutas,
  CRC, hashes y lectura posterior de cada archivo. Nunca escribe en datos de aplicaciones.

[Gate normal](evidence-jni-lab-v2-20261020/native-300.json) ·
[Gate -O](evidence-jni-lab-v2-20261020/native-300-opt.json).

### Defecto real corregido en el verificador incorporado concurrentemente

Al ejecutarlo contra la APK preservada, el verificador del propietario contabilizaba 85 ELF:
solo leía los `.so` planos situados en `lib/`, omitiendo los 12 de
`assets/chaquopy/bootstrap-native/arm64-v8a/`. Ahora inspecciona todos los `.so` planos y
mantiene la comparación estricta contra los **97 nombres y hashes fijados**. No se amplía
el inventario aceptado. Tres regresiones comprueban presencia, hash incorrecto y ELF extra;
el doble de APK reproduce ahora la distribución real 18+12. La ejecución física corregida
aprueba 97/97 totales y 96/96 ARM64. La APK no cambió.

[Resultado físico](evidence-jni-lab-v2-20261020/owner-candidate-physical-fixed.json) ·
[Reproducción del defecto](evidence-jni-lab-v2-20261020/concurrent-verifier-inventory-defect.json).

El informe de secciones conserva hashes por sección y resúmenes canónicos de los
385 símbolos, 58076 relocaciones y 447 rutas, en lugar de publicar cientos de miles de
líneas duplicadas. El analizador compara los registros completos de ambos ELF preservados.

### Repetir las comprobaciones host sobre los artefactos privados

Python3.11 con `pyelftools==0.33`; `$REPO` apunta a esta revisión y `$LAB` al directorio
privado recuperado. Ningún comando carga el JNI ni instala la APK:

```bash
python3.11 "$REPO/tests/native_compatibility/review_rebuilt_candidate.py" --apk "$APK"
python3.11 "$REPO/tests/native_compatibility/elf_candidate_review.py" \
  --linked "$LAB/jni-unstripped/libtmessages.49.so" \
  --packaged "$LAB/libtmessages-packaged.so" --output "$LAB/elf-review.json"
python3.11 "$REPO/tests/native_compatibility/review_candidate_v2.py" \
  --apk "$APK" --output "$LAB/new-private-v2-draft.json"
```

El último destino debe ser nuevo, fuera del repositorio y sin symlinks. Es un borrador
bloqueado, no un contrato aceptado por el runner. El análisis ELF completo puede emitir
más metadatos de depuración que el resumen publicado; las comparaciones se realizan antes
de resumir. Para el gate se requiere además JDK21 y los módulos fijados de PR20/PR21 en
`FLEXYGRAM_TEST_PR20`/`FLEXYGRAM_TEST_PR21`, como registran los logs de ejecución.

## Laboratorios: recursos preparados, ejecución pendiente

Se descargaron y verificaron **los archivos completos**, no solo las cabeceras HTTP:

| Perfil | Imagen oficial | SHA-256 | Estado |
|---|---|---|---|
| A | ARM64 API24 r09 | `3c3a70dcffe8c162984ec190fc3388bf237b241b3ba80bf7aa5c86e130d8f59b` | CRC/ABI/API/kernel y nueve archivos materializados verificados; AVD creado |
| B | ARM64 API35 ps16k r05 | `991c7c08258a0a32d7851ae8f9fb7dcd62f5b3907f1a91a2514cd94e75005cb3` | CRC/ABI/API/kernel gzip y 29 archivos materializados verificados; AVD creado |

Los AVD `flexygram-api24-offline-v2` y `flexygram-api35-offline-v2` se crearon con
`avdmanager`, exit0, y fueron enumerados por Emulator. Configuración sin claves duplicadas,
ARM64 y memoria2GB. **Ninguno se arrancó**: tamaño real de página y modo estricto siguen en null/no verificado.

Herramientas verificadas: Emulator37.2.12/build16428233 headless, motor ARM64,
ADB37.0.1 y Command-line Tools19. Se corrigieron ubicación canónica de CLI Tools y
registro del paquete Emulator desde metadatos oficiales, además del bit ejecutable
del `crashpad_handler` extraído. La consulta de versión se repitió tras esa corrección. Se conserva el aviso de CLI19
sobre XML SDK v4: no impidió crear estos AVD, pero no se presenta como validación completa
 de herramientas para Android37. Los metadatos y recetas se conservan para repetir la preparación.

Bloqueos actuales:

- `unshare --user --map-root-user --net true` falla por permisos del host. No hay aislamiento
  offline comprobado; por ello no se intentó arrancar el emulador.
- Sin KVM. Esto **no demuestra** imposibilidad de TCG, ni la presencia del motor demuestra
  que arranque Android ARM64. La prueba de TCG/boot sigue pendiente en un host aislable.
- El espacio local quedó por debajo de1GB tras materializar imágenes; no es un margen adecuado
  para iniciar perfiles con partición de datos2GB. No se borraron APK, wheels ni respaldos únicos.
- La autorización actual no permite generar claves, firmar ni instalar.

[Preflight real](evidence-jni-lab-v2-20261020/lab-host-preflight.json) ·
[AVD creados](evidence-jni-lab-v2-20261020/avd-prepared-v2.json) ·
[Procedimiento externo](LAB-V2-EXTERNAL-PROCEDURE.md).

## Revisión del candidato y firma

El candidato supera la revisión técnica host realizada; es razonable **presentarlo al
propietario como nuevo candidato para laboratorio**, sin exigir una coincidencia artificial
con la APK histórica. Esto no acredita ejecución, seguridad absoluta, beta o integración.

Se guardó privadamente un **borrador v2 no ejecutable**, vinculado a29188186… y al JNI756e53d2…,
con los 12 casos y18 wheels originales. Conserva certificado, APK firmada y runner firmado
en `null`; custodia, autorización de firma y activación permanecen `false`.
El contrato v1 conserva SHA-256
`1a3ecb0160e2babf91c9ef7c1712c3577fadb73c5f647d17d84275af146dbb28`.
No se modificaron sus pins ni sus adaptadores/runner para aceptar este candidato.
[Recibo v2](evidence-jni-lab-v2-20261020/v2-draft-receipt.json).

Antes de firmar faltan: aceptación del candidato por el propietario; custodia privada
recuperable de la identidad Diagnostic; autorización nueva y explícita para generación y
firma; certificado público medido; y adaptación v2 revisada del verificador post-firma y
runner/PR20/21. Los verificadores actuales v1 siguen ligados a sus hashes antiguos:
**no deben reutilizarse ni repinarse silenciosamente**. El permiso histórico condicional
registrado en `identity.pending.json` no sustituye la autorización de esta continuación.

La política propuesta existente RSA3072/PKCS12 es solo una especificación. La futura clave
no se reutilizará en Production; su contraseña debe custodiarse separada del almacén y del
respaldo cifrado. La recuperación debe demostrarse antes de firmar. No se generaron claves.
La firma futura puede aplicarse a los bytes unsigned conservados, sin reconstruir otra APK;
el gate v2 deberá verificar APKv2/certificado/zipalign y equivalencia del contenido ZIP.

Después quedan las pruebas reales de primer arranque, carga JNI/Python, 12 casos por perfil,
restauración sintética, permisos/componentes y tráfico por UID. Los bytes históricos del JNI,
si aparecieran, permitirían una comparación adicional; su ausencia debe seguir declarada.

Main/develop intactas, PR2 abierto, PR17 en borrador. Sin autenticación, servicios externos,
APK instalada/distribuida, Actions habilitado, optimizaciones del cliente ni Paso4.
