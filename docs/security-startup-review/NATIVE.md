# Bibliotecas nativas y relevancia para el arranque

Esta revisión reutiliza la auditoría real del archivo con SHA-256 `1ca683e5e4ef924ca9e7636afcd0c0b2c54de5064a46603ac5ae7b4f811278fe`, cuyo hash se recalculó en la presente investigación. Se conservan las evidencias anteriores de readelf, CRC, firma y zipalign; no se presentan como nuevas pruebas de ejecución. Los datos estructurales relevantes se incluyen en evidence.json para trazabilidad.

## Resultado y alcance

| Comprobación anterior | Resultado | Límite |
| --- | --- | --- |
| Arquitectura instalada | Solo `lib/arm64-v8a`, 18 ELF | No equivale a probar cada dlopen/JNI_OnLoad |
| ELF en APK y contenedores Python | 97 ELF: 96 AArch64 y un auxiliar Linux amd64 de debugpy en assets | El auxiliar de herramientas no convierte la APK en instalable x86_64; no se ejecutó |
| PT_LOAD de las 18 bibliotecas raíz | Superan el criterio estructural de alineación 16 KB | No certifica código interno, relocalizaciones, imports o funcionamiento |
| Python, cuatro bibliotecas | `libexslt.so`, `libfreetype.so`, `libxml2.so`, `libxslt.so`: PT_LOAD con alineación 4096, no cumplen el criterio ELF 16 KB | Compatibilidad plena 16 KB no certificable, aunque un sistema pueda ofrecer modo de compatibilidad |
| GNU_RELRO | 73 finales no múltiplos de 16 KB; solo 3 con solapamiento adicional de secciones escribibles no padding: exslt, xml2, xslt | 73 avisos no significan 73 fallos. Los otros 70 tampoco quedan certificados solo por no mostrar ese solapamiento |
| Dependencias DT_NEEDED | Ninguna ausente según inventario APK/Python y allowlist de bibliotecas de sistema | El namespace del linker, disponibilidad por API y orden de carga no se prueban con una allowlist |
| Integridad | CRC APK y seis IMY correcto; sin cabeceras pyc truncadas detectadas; hashes ELF registrados | No es auditoría semántica de paquetes Python ni prueba de sus imports en Android |
| Firma/empaquetado | v2 válida, zipalign anterior correcto | ZIP alignment no arregla ELF ni los archivos extraídos desde IMY |

Las cuatro bibliotecas están en `assets/chaquopy/requirements-common.imy!chaquopy/lib/`, no en las 18 bibliotecas JNI raíz. La lectura ELF exige revisar p_align, tamaños y congruencia de p_vaddr/p_offset de **cada PT_LOAD**. Cambiar padding ZIP o editar el número p_align no reconstruye los segmentos ni arregla sus dependencias.

El análisis de RELRO consideró el intervalo protegido redondeado a páginas de 16 KB y si las secciones SHF_ALLOC|SHF_WRITE fuera de RELRO compartían esas páginas. Se encontró `.data` para exslt y `.data/.bss` para xml2/xslt: riesgo adicional concreto de protección de memoria. No se convirtió un final RELRO sin redondear, por sí solo, en un crash confirmado. El comportamiento final depende del linker/modo del dispositivo y necesita prueba Android.

`libxml2/libxslt/libexslt` participan en el conjunto de dependencias de lxml y `libfreetype` en la pila de fuentes/Pillow. Tener paquetes presentes no prueba que se importaran durante el arranque observado. El motor Python está desactivado por defecto y su inicio explícito se publica a un worker; una instalación restaurada puede tenerlo habilitado. Debe trazarse el import exacto antes de vincular esos binarios a un fallo o demora.

## ¿Explican la lentitud?

No hay evidencia de ello. Una incompatibilidad de carga puede causar error de linker, import fallido o cierre cuando se usa la biblioteca. No demuestra un arranque lento; tampoco se asume que cada fallo produzca reintentos. En un sistema 4 KB, el hallazgo específico de alineación 16 KB no basta para explicar el comportamiento observado. Aun en 16 KB, hay que comprobar biblioteca efectivamente cargada, resultado y modo de compatibilidad, sin deducirlo del modelo del teléfono.

El host de las herramientas usaba páginas 4096. Ese dato **no describe el Poco**. No hay Android conectado ni emulador disponible en las evidencias de ejecución; instalación, pantalla, carga Python/JNI y Logcat no se realizaron aquí. El teléfono instalado por el usuario constituye otro entorno y no se ha recibido su `getconf PAGE_SIZE`.

## Resolución propuesta, sin implementar

1. Mantener la base y los binarios actuales como evidencia; no quitar dependencias ni parchear cabeceras ELF para esconder alertas.
2. Identificar versiones, wheel exacto, build recipes, toolchain y licencias del conjunto lxml/Pillow y sus dependencias. Elegir actualización o reconstrucción de todas las piezas afectadas, con ABI Python/JNI compatibles y pin de hashes/versiones.
3. Revisar tamaño de página en código de memoria/mmap y no solo flags del linker; conservar API/semántica de las dependencias. La revisión actual no certifica todas las suposiciones de 4096 bytes en el código.
4. Repetir readelf PT_LOAD/RELRO/DT_NEEDED, inventario y zipalign del resultado; ejecutar imports y ejercicios sintéticos de XML/XSLT/fuentes en entornos Android ARM64 limpios, 4 KB y 16 KB, tras aprobación y con identidad independiente.
5. Separar éxito en modo de compatibilidad 16 KB de soporte nativo completo; registrar cualquier ajuste del sistema sin recomendarlo como arreglo permanente.

La [guía oficial de Android para 16 KB](https://developer.android.com/guide/practices/page-sizes) distingue alineación ELF, empaquetado y errores de código en ejecución. Recomienda comprobar el tamaño real con `adb shell getconf PAGE_SIZE` y comprobar ZIP con `zipalign -c -P 16 -v 4`. Esos criterios orientan pruebas posteriores; no representan mediciones de este Poco.
