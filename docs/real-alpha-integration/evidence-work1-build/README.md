# Work 1: realAlpha ARM64 compilada y revisada estáticamente

Base PR #50: `b5575029dde6bf787bf0781dcfd032256789ee26`.
Código de aplicación compilado: `38e9052242988cdcb0771df816a4769990cac547`.
Verificadores y receta: `e21f1fdbab73005bbca680af63613b23a605b227`.

- Build ARM64 completo con JNI/Chaquopy: **BUILD SUCCESSFUL**; primera compilación 10m04s, empaquetado final 1m08s.
- APK unsigned: **124.452.770 bytes**; SHA-256 `cc2053f96119dca5319d9a02bb2ece9a49b7cc342747e975103c4bfba5e8520b`.
- 107 pruebas host distintas PASS; las 18 del gate combinado también PASS con `-O`.
- 96/96 ELF Android ARM64 válidos para 4 KB/16 KB; 0 imports fuertes, dependencias o versiones sin resolver. El ELF x86_64 restante es el asset Linux de debugpy fijado, no una biblioteca Android instalable.
- Identidad realAlpha independiente, sin INTERNET, API ID 0, hash vacío, seis capacidades externas deshabilitadas; firma ausente y zipalign16 KB correcto.
- DEX: host de login, ensayo local, sesión local e interfaz offline definidos; comprobados bindClosedLocalPages, offlineAwareEmptyView, cancelOfflineSearch y searchOfflineDialogs. Limpieza/delegación de ciclo de vida verificadas con --combined-local-login.
- Cuatro ELF y tres wheels reconstruidos coinciden con pins históricos y salidas independientes. Los otros 15 wheels no cambian. La ruta NDK histórica en DWARF se reproduce desde fuente, sin editar ELF ni relajar hashes.
- Respaldo privado: **268.711.319 bytes**, SHA-256 `31702d7c98d8d5042e9022ffa3325d0b5b42dc6bd41d5f920d7a65a84ac56cb8`; 45 miembros con CRC y SHA-256 verificados. Copia guardada recuperada íntegramente y verificada de nuevo, incluida la APK.

Gradle 9.7.1, JBR daemon 21.0.10 (launcher/host JDK 21.0.13), Python3.11.17, SDK37.0r2/35/24, BuildTools36.0.0, NDK27.2.12479018, CMake3.31.6 y Chaquopy17. Submódulos fijados recuperados, sin sustituciones de dependencias. El overlay de wheels se aplicó con prepare_experiment sobre un checkout aprobado independiente; conserva el gate combinado y se guardó su hash. Configuración original restaurada después del build.

Se conservan advertencias heredadas y un aviso de strip sobre un archivo temporal intermedio; el APK verificado no contiene esos temporales. Los logs publicados solo normalizan la ruta local; evidence-sha256.json distingue sus hashes originales.

**No instalado, no ejecutado en Android, no firmado, no fusionado.** No acredita fluidez ni funcionamiento Android. APK y respaldo no se publican en GitHub. main/develop y los PR originales permanecen intactos.
