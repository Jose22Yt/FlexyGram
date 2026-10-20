# P0.4c — experimento aislado de reconstrucción 16 KB

Base conservada: `a25295a9d567a626e008fc55ca97d80112c5f65b`, PR17 en borrador. No se modifica la dependencia activa del Diagnostic aprobado. No se fusiona ningún PR, ni se autoriza beta/Production/distribución. Identidad de FlexyGram: @Lukhou23; se mantienen GPL, créditos y avisos originales.

## Contratos y cambios acotados

Las tres distribuciones siguen en FreeType2.9.1, libxml2 2.9.8 y libxslt1.1.32 (incluye EXSLT). Se reconstruye XZ/LZMA5.2.4 estático, como en libxml2 original; zlib sigue siendo la biblioteca de plataforma. El callback de libxslt recibe `const xmlChar*` para concordar con la API pública de xmlHashScanner; solo cambia un parámetro no utilizado. No se elimina ninguna función ni biblioteca. Versiones y orígenes de fuentes: `tools/native_compatibility/rebuild-sources.json`.

Los primeros candidatos LLD conservaban las funciones públicas, pero perdían símbolos absolutos GNU/etiquetas históricas y herencia entre definiciones de versiones. La comparación nueva **añade** comprobación de tipos, binding, visibilidad, tamaño de datos y grafo GNU; no relaja `acceptance.py`. La receta final usa GNU ld2.42 compilado desde fuente únicamente para enlazar las tres bibliotecas XML. Archivo oficial: `https://ftp.gnu.org/gnu/binutils/binutils-2.42.tar.xz`, SHA256 `f6e4d41fd5fc778b06b7891457b3620da5ecea1006c6a4a41ae998109f85a800`. Se fija el archivo recibido por HTTPS; no se afirma verificación GPG. No se cambia el enlazador del cliente Android ni del resto de dependencias.

GNU conserva objetos absolutos y padres de versiones; un fragmento de script de enlace reconstruye etiquetas de límites conforme a las secciones nuevas, sin copiar direcciones antiguas. `--as-needed` se aplica exclusivamente a la entrada libz de XSLT/EXSLT para conservar sus edges originales, a través de libxml2. Se conservan todos los objetos y archivos estáticos. Se conserva también el orden exacto de DT_NEEDED: libm se coloca antes de libxml2 en XSLT/EXSLT y antes de libz en FreeType. Ambas tablas de hash ELF originales (.hash y .gnu.hash) se generan de nuevo. `--undefined-version` permite los nombres obsoletos del mapa de fuente (DocBook/xmlDllMain) que ya no producían funciones; la comparación exige conservar todos los símbolos que **sí existen** en el original. Los imports fuertes se verifican por separado en el conjunto empaquetado contra API24.

Los stubs NDK27 contienen DWARF zstd. GNU construido sin la biblioteca zstd host no los leía. Se descomprime **solo la información de depuración en copias aisladas de los stubs**, mediante llvm-objcopy del NDK fijado. Se verifica igualdad de símbolos/versiones/etiquetas dinámicas antes/después. No se modifica el NDK original ni se parchea ningún ELF del APK; ningún stub se distribuye. `MAKEINFO=true` evita generar documentación del linker porque falta makeinfo; no omite código de biblioteca o verificación ABI.

Reproducibilidad: prefix-map de compilador para rutas de fuente; argumento explícito CMAKE_C_FLAGS en FreeType, ya que la configuración Android de CMake no heredaba CFLAGS. El directorio por defecto de plugins XSLT se conserva exactamente del binario original, aunque contiene una antigua ruta de construcción que no opera en Android; no se reemplaza por una ruta escribible ni se desactiva soporte de módulos para obtener igualdad. Cambiar ese default requeriría una revisión funcional separada. Los perfiles configurados conservan XML con HTTP/FTP, módulos, hilos, zlib/LZMA, XSLT sin crypto/Python y FreeType con zlib, sin HarfBuzz/PNG/BZip2. En el original, FT_Stream_OpenBzip2 y FT_Library_SetLcdFilter ya retornaban error7; no son funciones retiradas por este cambio. El corpus de formatos y comportamiento completo sigue pendiente en Android.

## Wheels experimentales

`experimental_wheels.py` conserva exactamente todos los miembros del wheel original salvo cuatro ELF, WHEEL y RECORD. Mantiene METADATA, licencias, cabeceras, créditos y dependencias. Etiqueta de construcción distinta `3flexygram16k` y plataforma **android_24_arm64_v8a**, acorde al mínimo real; no anuncia API21. ZIP ordenado, fecha y permisos fijos, hashes RECORD recalculados. No se ofuscan claves ni identidades. Las cuatro bibliotecas y los tres wheels se compararon byte a byte entre dos directorios independientes.

Los26 wheels originales y sus hashes permanecen intactos. El experimento selecciona18 ARM64, reemplaza3 wheels y conserva15 sin cambios. No hay sustitución x86_64 propuesta. Los hashes nuevos y comparación detallada están en `evidence-16k-experimental/wheel-reproducibility.json` y `abi-report-final.json`. Los wheels y APK permanecen internos, no se adjuntan ni distribuyen. Las regeneraciones sucesivas deben utilizar destinos nuevos e inmutables; una discrepancia de hash/inventario en una carpeta reutilizada bloqueó la preparación, sin relajar el verificador. --wheel-output permite un destino nuevo al repetir la finalización; los dos conjuntos finales se verificaron íntegramente.

## Reproducción offline

Disponer de checkout completo, submódulos fijados, Python3.11 con el lock de herramientas, JDK21/Gradle9.7.1/AGP9.3.1/SDK37/BuildTools36.0.0/NDK27.2.12479018/CMake3.31.6/Chaquopy17 originales. Preparar los archivos fuente exactos del manifest, FreeType en el commit declarado y el archivo binutils anterior. La fase de descarga se realiza separadamente desde esos orígenes; la receta rechaza hashes distintos y no descarga durante build.

Ejemplo de variables locales (sin secretos): `SRC` contiene las fuentes verificadas; `OLD` los26 wheels; `NDK` y `CMAKE` las herramientas fijadas; `WORK` es un directorio temporal fuera del checkout; `PY` es Python3.11 con pyelftools. La firma propia se aporta solo por entorno privado, sin imprimir ni guardar contraseñas en Git.

```sh
"$PY" tools/native_compatibility/experiment_recipe.py --build-linker --sources "$SRC" --output "$WORK/gnu"
"$PY" tools/native_compatibility/rebuild_candidates.py --sources "$SRC" --output "$WORK/a" --ndk "$NDK" --cmake "$CMAKE" --wheelhouse "$OLD"
"$PY" tools/native_compatibility/experiment_recipe.py --sources "$SRC" --output "$WORK/a" --ndk "$NDK" --cmake "$CMAKE" --wheelhouse "$OLD" --linker "$WORK/gnu/build/ld/ld-new"
```

Repetir las dos últimas órdenes para `$WORK/b` y comparar los cuatro `.so` y los tres wheels, más manifests. La salida intermedia `report.json` de rebuild_candidates corresponde a LLD antes de finalizar, no sustituye `compat-report.json` y la comparación final. No presentar el estado intermedio como candidato aprobado.

Crear otro worktree **detached del commit base**, sin tocar la rama principal. Inicializar todos sus submódulos a sus SHA fijados. En la ejecución documentada se reutilizaron las fuentes de los16 submódulos mediante enlaces locales a los checkouts fijados ya existentes; se registró su inventario. El build y .cxx del cliente pertenecen al checkout experimental. Las fuentes de submódulos se comparten, no se afirma un sandbox de lectura estricta.

```sh
"$PY" tools/native_compatibility/prepare_experiment.py --source "$CHECKOUT" --checkout "$EXPERIMENT" --wheelhouse "$WORK/a/wheels" --manifest "$WORK/a/wheels-manifest.json" --python "$PY"
NATIVE_TARGET=arm64-v8a ./gradlew -p "$EXPERIMENT" --offline --no-daemon -Pkotlin.incremental=false :TMessagesProj:assembleDiagnosticDebug
```

El overlay cambia únicamente ubicaciones de requirements/wheelhouse y la verificación offline previa a pip en **el build.gradle del checkout desechable**. Los build.gradle/locks activos, políticas de variante, manifiestos, clases, JNI y código funcional permanecen iguales. El conjunto de requirements experimental conserva18 versiones, exige los hashes nuevos y solo encuentra los18 wheels locales verificados; no existe fallback a índices. Build/ABI solo ARM64. No se habilita ninguna capacidad ni se crea variante productiva.

En esta ejecución hubo un build completo con un overlay LLD intermedio mientras se completaba la comparación ampliada; después se forzó la reinstalación Python de los wheels finales GNU y se repitió assemble. Los logs de ambos pasos se conservan y la APK final se comprueba por los hashes de los cuatro ELF internos. No se atribuye la APK intermedia a los wheels definitivos.

Pruebas de host, ejecutadas separadamente: `build_host_fixture.py --workspace <directorio-de-insumos>` construye las mismas versiones fuente para Linux. `runtime_cases.py --libdir <host-prefix/lib> --freetype <host-ft/libfreetype.so> --font <fixture>` ejecuta12 casos, usando además wheels **manylinux** lxml5.3.0/Pillow11.0.0. No ejecuta los ELF ARM64. Las fuentes tipográficas, versiones reales de bibliotecas y límites constan en el log. Para certificación se necesita el laboratorio de `ANDROID-LAB-16K.md`.

## Alcance de aceptación

Un resultado estático limpio significa condiciones necesarias de PT_LOAD, RELRO y resolución API24; **no certifica Android**. Funciones internas, weak symbols, dlopen, namespaces, formatos de fuentes, JNI/ART/Chaquopy y comportamiento de carga deben probarse en ambos laboratorios. Mantener el PR17 en borrador y no promover el overlay a dependencias activas antes de esa validación y revisión explícita. No modifica navegación, animaciones, interfaz, rendimiento ni datos/sesiones.
