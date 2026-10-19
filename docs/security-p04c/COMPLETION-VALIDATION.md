# P0.4c — validación disponible completada; beta/16 KB todavía bloqueadas

Responsable: @Lukhou23. Esta continuación recupera el PR #17 en el HEAD exacto **`9b38f4390311adbf337815828b0e5f720904d576`**, rama `security/paso-3-p04c-completion-review`. Se conserva íntegramente su trabajo previo. **No se recomienda fusionar ni distribuir todavía:** cuatro ELF activos siguen siendo de 4 KB y no existe un laboratorio Android ARM64/16 KB disponible en este entorno.

Este informe sustituye el estado de validación parcial anterior, sin borrar los documentos o evidencias históricos. No modifica main/develop ni fusiona PR. No se inicia el Paso 4.

## Resultado actual

| Verificación | Resultado de esta ejecución |
|---|---|
| Checkout / submódulos | Git íntegro, HEAD revisado y 16 submódulos en sus commits fijados |
| Puerta original P0.4c antes de esta continuación | **42/42**, cero fallos y cero omisiones, con Python3.11.17 y pyelftools0.33 |
| Nuevos controles de aceptación/reconstrucción | **11 pruebas** adicionales |
| Puerta final `python tests/native_compatibility/run_gate.py` | **53 aprobadas, 0 fallidas, 0 omitidas**, repetida también con `python -O` |
| Regresiones P0.4b | **102 aprobadas en una ejecución nueva**, 0 fallidas, 0 omitidas; siete logs nuevos |
| Total P0.4c + históricas | **155 aprobadas**, sin sumar dos veces las repeticiones o los PR auxiliares |
| Python runtime | **18 paquetes fijados, 26 wheels reales**, todos los hashes y CRC verificados; 18 seleccionados por ABI |
| Instalación cruzada pip | 18/18 ARM64 y 18/18 x86_64 desde wheelhouse local, `--no-index --require-hashes --only-binary`; no equivale a importarlos en Android |
| Gradle Diagnostic ARM64 completo | **BUILD SUCCESSFUL, exit0, 17m13s**; 249 tareas: 213 ejecutadas y 36 desde caché |
| JNI / Chaquopy | CMake/Ninja ARM64 y runtime Python reconstruidos, sin SKIP; pip Chaquopy instaló los 18 pins desde el wheelhouse verificado |
| Production | `assembleProductionRelease` rechazada realmente, **exit1**, con `FLEXYGRAM_PRODUCTION_INCOMPLETE`; no APK productiva |
| APK y manifiestos | Identidad diagnóstica, API0/hash vacío, capacidades cerradas, **sin INTERNET**, firma Debug propia válida |
| Seguridad estática APK/dependencias | Escaneos completos aprobados; cero claves/marcadores retirados; no clases de transporte ficticio |
| JNI real | Tres entradas solo RET, scope Java/JNI coincidente y sección .text del enlazado idéntica a la empaquetada |
| Resolución estática API24 | **96 ELF ARM64**, cero DT_NEEDED ausentes, cero imports fuertes sin resolver y cero discrepancias de versión de proveedor |
| Alineación ELF | **96/96** pasan 4 KB; **92/96** pasan 16 KB; los cuatro históricos siguen bloqueados |
| Android / carga real | **No ejecutado**: host x86_64, sin emulador instalado, sin KVM y sin dispositivos ADB |

Los retornos1 de la puerta estática nativa y de Production son **bloqueos esperados**, no pruebas aprobadas ni fallos de unittest ocultos. Los fallos de los PR auxiliares se describen por separado.

## Identidad exacta del código y artefacto

Código Android/JNI, Gradle, manifiestos, políticas, módulos y locks realmente compilados: **`9b38f4390311adbf337815828b0e5f720904d576`**. Después de compilar se verificó que esta continuación no los cambió. Los commits posteriores solo añaden herramientas/pruebas y evidencias; no se les atribuye una segunda APK inexistente.

- APK **interna**, sin adjuntar/instalar/distribuir: SHA256 **`40cac89aeb2087e9a467b04fc6a6fad2d7b1651482f8ed65fa053665e9d491d1`**.
- Tamaño: **111959935 bytes**. Etiqueta `FlexyGram Diagnostic`, paquete `io.github.jose22yt.flexygram.diagnostic`, versión13.0.2/1261, ABI arm64-v8a.
- Firma Debug v2 verificada. Certificado propio de esta sesión: SHA256 **`27ef63ae50546c0af28c0ac54ef66a0c00614934cda86c6bea42d9d2759e7b83`**. Se generó otra clave de laboratorio porque la anterior no estaba disponible; no se afirma continuidad de actualización ni firma definitiva. La clave/contraseñas quedan fuera de Git.
- El manifiesto fusionado y el binario pasan la allowlist; solo ACCESS_NETWORK_STATE y permiso propio del receptor no exportado. No INTERNET. API ID0, hash vacío, aislamiento y seis capacidades falsas en BuildConfig real.
- Scope Java/JNI `0f92362819e8a4973909188235d68012a364c974d8e430ce61370e88da8ed181:diagnostic`; exportación nativa de política verificada. init y ambas aperturas de socket constan únicamente de RET. El target real de los comandos nativos es `aarch64-none-linux-android24`, además del valor CMake.
- Scan: 14858 entradas, 7 archivos anidados; cero candidatos de clave cliente, claves retiradas, paquete/certificado ajeno registrado o google-services.json. Los artefactos externos resueltos y JAR fuente se escanean también; ver inventario íntegro en `artifact-scan.json`. No se promete ausencia universal de secretos por un escaneo estático.
- `zipalign -c -P 16 -v 4` pasó; **no** demuestra alineación ELF ni carga real de bibliotecas extraídas de IMY.

## Correcciones y trabajo añadido en esta continuación

No hubo errores de compilación de la aplicación que justificaran modificar su lógica. Se conservan API24, locks, auditor ELF, hardening del wheelhouse y gate anteriores.

1. `tools/native_compatibility/acceptance.py`: separa aceptación estática del APK y revisión conservadora de candidatos. Rechaza 4 KB, imports/dependencias/versiones no resueltos, solapamiento RELRO escribible y diferencias de contratos que necesitan revisión. Incluso un resultado estático limpio mantiene `runtime_required=true` y `distribution_allowed=false`.
2. `rebuild_candidates.py` y `rebuild-sources.json`: reconstrucción **offline y aislada** de los cuatro candidatos, con NDK27.2.12479018, API24 y fuentes/versiones/hashes explícitos. No modifica wheelhouse activo, locks, APK ni dependencias. Comprueba archivos fuente, commit FreeType, wheel original, directorios sin symlink, entorno sin contaminación de includes/librerías host y parche exacto de callback. Las fuentes se compilan, no se cargan.
3. Once pruebas sintéticas nuevas verifican el rechazo de pérdidas de exports/versiones, dependencias/SONAME/máquina/API incorrectos, alineación, RELRO, ausencia de target, hashes/symlinks, parche exacto y contrato del lock original.
4. `reviewed_changes.json` incorpora únicamente los tres nuevos archivos de herramientas con hashes congelados. No se regeneran hashes dentro de las pruebas ni se debilitan snapshots históricos.

Navegación, animaciones, renderizado, preferencias, interfaz, actualizador, autenticación y políticas Java/JNI quedan intactos. Se conservan autorías/licencias originales y la identidad de @Lukhou23.

## 16 KB: problema activo y reconstrucciones verificadas

La nueva APK incluye **97 ELF**: 96 AArch64 y un payload auxiliar x86_64 de debugpy, que permanece visible en el informe y no se cuenta como biblioteca Android ARM64. El análisis recorre también los IMY, no solo `lib/`.

| ELF activo de Python | PT_LOAD16KB | Observación |
|---|---|---|
| libexslt.so | No | 4 KB; familia chaquopy-libxslt1.1.32 |
| libfreetype.so | No | 4 KB; chaquopy-freetype2.9.1 |
| libxml2.so | No | 4 KB; chaquopy-libxml2.9.8 |
| libxslt.so | No | 4 KB; familia chaquopy-libxslt1.1.32 |

Los cuatro también presentan contenido escribible en el redondeo RELRO reportado. Esto requiere resolución y carga real en16KB; no se declara un crash demostrado. El resto no se marca como defectuoso únicamente por una terminación RELRO no alineada sin solapamiento.

Se consultaron los índices oficiales Chaquopy de esas tres distribuciones: no se encontró un build ARM64 posterior al2 que solucionase el problema. No se inventó una URL/version ni se sustituyó el lock por un paquete de otro origen. Índices y nombres disponibles quedan en `native-candidates.json`.

### Experimento de reconstrucción real — no empaquetado

Se ejecutó el script publicado y se reconstruyeron **los cuatro ELF**, con las mismas versiones y flags `max-page-size=16384`/`common-page-size=16384`. Los cuatro candidatos pasan PT_LOAD4KB/16KB y declaran API24. Sus hashes, comandos y diferencias están en `source-rebuild-final.json`.

- **FreeType2.9.1**: fuente Git versionada en `86bc8a95056c97a810986434a3f268cbe67f2902`, CMake Android, misma SONAME y199 pares exportados conservados, sin DT_NEEDED nuevos. Pasa la comparación estática conservadora. Esto **no** acredita paridad de opciones de compilación, formatos de fuente o carga Android; no se incorpora al APK.
- **libxml2.9.8**: fuente GNOME con checksum oficial. El primer intento sin LZMA se rechazó: el original lleva **XZ/LZMA5.2.4 estático**, aunque no aparezca como DT_NEEDED. Se obtuvo y reconstruyó esa fuente versionada y se repitió con LZMA, evitando eliminar esas funciones. El candidato final conserva las funciones, pero la comparación estricta sigue señalando diferencias en nodos exportados de versión GNU y etiquetas de límite del enlazador. **Esas diferencias no se presentan como pérdida demostrada de funciones públicas.** Necesitan clasificar/versionar el ABI y probar consumidores antes de sustituir.
- **libxslt/libexslt1.1.32**: reconstruidos contra esa libxml2. NDK27 detectó un callback cuyo parámetro no coincidía con el `const xmlChar*` esperado; el experimento corrige solo la firma del parámetro ignorado, sin suprimir la categoría de errores del compilador. Hay diferencias de nodos de versión/etiquetas y DT_NEEDED directo `libz.so` añadido (ya transitivo vía XML). La puerta conservadora exige revisar esas diferencias; no prueba por sí sola incompatibilidad funcional.
- El enlazador moderno también detectó entradas antiguas del version-script referidas a símbolos no definidos. El experimento registra `--undefined-version`, que permite construir ese mapa antiguo; no autoriza ignorar imports reales ni pérdidas de API. La comparación posterior permanece estricta y bloquea la sustitución automática.

**No se ha integrado ninguno de estos binarios.** No se han editado/reempaquetado ELF de4KB para hacerlos parecer de16KB, ni se han quitado bibliotecas/funciones para pasar el escáner. El runtime lock original se conserva. La vía concreta recomendada es completar la revisión de versiones GNU/contrato y opciones, construir wheels identificados y hash-pinned de esas fuentes, probarlos con lxml/Pillow en Android, integrarlos con trazabilidad y repetir APK/ELF/regresiones. No basta con cambiar p_align o usar zipalign.

## PR auxiliares: pruebas reales y recomendación

Se revisaron en worktrees separados, sin fusionar ni modificar sus ramas. Git merge-tree no detecta conflictos textuales contra develop ni contra el HEAD revisado de P0.4c. Los gates de alcance congelado de P0.4c sí requieren una actualización explícita antes de integrar cambios auxiliares; no deben ampliarse indiscriminadamente.

| PR / HEAD revisado | Resultado comprobado | Recomendación |
|---|---|---|
| #16 / `fe3b8973b44a74fcbba3aedc92a514f3b1462e80` | 8 pruebas pasan; auditor --strict exit0, cero errores y10 elementos de revisión | Integrable como auditor/documentación tras P0.4c y revisión de alcance; no trata nombres internos/créditos como errores a borrar |
| #18 / `44f9826e2d5d74634a85374962da07b068f39efa` | 6 pruebas pasan; nombres nuevos de8 locales y XML candidatos compilan aisladamente con AAPT2 | Favorable para nombres/recursos candidatos tras build Android del PR e integración revisada. **Icono no aprobado como predeterminado ni activado** |
| #19 / `4d128c682fe4cacb89ec3571e5e59fc05f6fa457` | Comando de pruebas documentado falla al importar audit. Con PYTHONPATH corregido:13 casos,11 pasan,1 fallo y1 error. Auditor encuentra11/11 señales pero --strict termina en TypeError | **No integrar todavía.** Corregir importación independiente, retorno booleano y falso positivo entre cuerpos de métodos; repetir13 tests/strict |

En #19 `int(args.strict and (lista or lista))` recibe una lista cuando debería convertir un booleano. Además, la mutación que retira la guarda de presentFragment no se detecta: el regex puede alcanzar una guarda de otro método en su ventana. Debe acotarse al cuerpo del método y conservar la prueba negativa. No se atribuye latencia real a estas señales ni se modifican animaciones/watchdog.

La compilación AAPT2 cruda de todo values/strings.xml de #18 falla en líneas heredadas **también presentes en develop**; no se atribuyen al PR de nombres. Se compilaron por separado los dos strings modificados de cada local y los XML del icono candidato. Es validación de esos recursos, no build Android completo de #18. Ningún manifiesto/launcher fue cambiado para activar el candidato.

## Laboratorio Android y límites

Inventario real: host x86_64, `/dev/kvm` ausente, sin ejecutable de emulador ni imágenes/laboratorio ARM64, `adb devices -l` vacío. **No se realizaron instalación, arranque, carga JNI/Python, comprobaciones de permisos en ejecución ni pruebas16KB.** No se instaló en teléfonos personales ni se conectaron cuentas/credenciales.

La resolución estática API24 es favorable para los símbolos y versiones inspeccionados, pero no certifica dlopen/dlsym, namespaces, callbacks, rutas ejecutadas, seguridad total ni funcionamiento del Poco X8 Pro/API37. No hay mediciones de rendimiento nuevas.

## Reproducción y entorno

Herramientas: JBR/JDK21.0.10 declarado, Gradle9.7.1 del Wrapper (distribución verificada con SHA256 oficial), AGP9.3.1, SDK37, BuildTools36.0.0, NDK27.2.12479018, CMake3.31.6, Python3.11.17, Chaquopy17.0.0 y pyelftools0.33 instalado con su hash. Se preparó también android.jar API24 para las pruebas. Sin cambios arbitrarios de versiones del proyecto. Los logs/versiones/hashes exactos están en `evidence-completion/`.

El entorno efímero anterior no existía; se recuperó el repositorio completo y se aprovisionaron herramientas desde fuentes oficiales. Se usó un puente proxy local solo para descargas de herramientas, sin publicar sus credenciales. La CLI Android más reciente había cambiado de comportamiento; se utilizó CLI19 verificada para instalar los SDK declarados, sin cambiar compiladores/SDK del proyecto. Los primeros arneses fallaron por CMake en PATH y caché Wrapper/Groovy ausentes; después de aprovisionarlos se repitieron las suites completas y pasaron. No se sustituyeron sus controles por omisiones.

Configurar JAVA_HOME y PATH para JBR/bin y SDK/cmake/3.31.6/bin; GRADLE_USER_HOME, GSON_JAR2.14.0, KOTLIN_LIB=Gradle9.7.1/lib, TRANSLATOR_CLASSES_JAR (oráculo ABI original verificado, nunca dependencia Android), ANDROID_SDK_ROOT, CHAQUOPY_BUILD_PYTHON y CMAKE. Firma de laboratorio mediante variables privadas ya definidas por el proyecto; no escribir sus valores en logs o Git.

```sh
python3.11 -m pip install --require-hashes -r tools/native_compatibility/requirements.lock
python tests/native_compatibility/run_gate.py
python -O tests/native_compatibility/run_gate.py
python -m unittest discover -s tests/security -v
python -m unittest discover -s tests/translation_safety -v
python -m unittest discover -s tests/translation_runtime -v
python -m unittest discover -s tests/translation_dependency -p test_prototype.py -v
python -m unittest discover -s tests/translation_dependency -p test_facade.py -v
python -m unittest discover -s tests/translation_staging -v
python -m unittest discover -s tests/build_variants -v
NATIVE_TARGET=arm64-v8a ./gradlew --no-daemon -Pkotlin.incremental=false :TMessagesProj:assembleDiagnosticDebug
./gradlew --offline --no-daemon :TMessagesProj:assembleProductionRelease  # debe rechazar
```

La construcción real utilizó el ejecutable de la distribución9.7.1 verificada, equivalente al Wrapper declarado. Las compilaciones/pruebas tienen logs nuevos; no se reutilizó el resultado102 histórico ni el APK P0.4b. Kotlin incremental se desactiva solo en la línea de comandos; no se declara resuelta su incidencia histórica.

```sh
python tools/native_compatibility/audit.py --apk APK_INTERNA --ndk NDK27 --output native.json
python tools/native_compatibility/acceptance.py --output native-acceptance.json artifact --report native.json
# La segunda orden devuelve1 mientras estén los cuatro ELF activos de4KB.
python tools/native_compatibility/rebuild_candidates.py --sources FUENTES_VERIFICADAS \
 --output DIRECTORIO_NUEVO --ndk NDK27 --cmake SDK/cmake/3.31.6/bin/cmake --wheelhouse WHEELS_ORIGINALES
```

El último comando se ejecutó realmente y produce candidatos/JSON/logs, **no wheels ni APK**, conservando los originales. El manifiesto de fuentes contiene URLs/hashes y commit FreeType. `requirements.lock` y los hashes de26 wheels originales no cambian.

## Qué falta para la siguiente fase

1. Cerrar la sustitución trazable de los cuatro ELF activos: resolver diferencias de metadatos/versionado y dependencias, revisar opciones/formato, empaquetar wheels reconstruidos con hashes y repetir los155 controles/build/scan.
2. Obtener laboratorio ARM64 API24 y moderno16KB: carga real JNI/Python y fixtures lxml/XSLT/fuentes/Pillow, instalación/arranque offline, crashes/ANR y permisos/tráfico por UID sin cuentas. Las verificaciones estáticas no sustituyen ese gate.
3. Revisión del propietario antes de fusionar PR #17; mantener pendientes las integraciones auxiliares hasta sus correcciones/validaciones.
4. La beta autenticable requerirá otra etapa autorizada: configuración privada propia de Telegram, firma e identidad de distribución y revisión de servicios. Production permanece bloqueada y no se habilita aquí.

**Resultado: validaciones disponibles completadas y solución por fuentes investigada/compilada, pero P0.4c no debe presentarse como certificado para16KB ni como una beta lista.** No fusión automática, no APK distribuida, no Actions, no Paso4.
