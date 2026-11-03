# Corrección de blur y perfil de rendimiento

Se conserva la personalización Signature de la beta. El desenfoque estándar usa
`FLAG_CHAT_BLUR`; la refracción de Liquid Glass permanece desactivada. Antes,
varias superficies dependían todavía del interruptor retirado, por lo que no
actualizaban o dibujaban su fondo aunque el desenfoque estuviera habilitado.

## Cambios

- Cabecera y compositor de conversación: restaurado el acceso a las fuentes de
  desenfoque estándar, sin reactivar la refracción.
- Barra inferior principal: reutiliza la fuente ya capturada y desenfocada del
  fragmento visible. Se elimina el redibujado del ViewPager y otro pase de blur.
- Controles superiores y carpetas: fondos reutilizables conectados a la fuente
  de la pantalla, con colores de tema y reserva opaca cuando no hay blur.
- Confirmación del número: el cálculo CPU del desenfoque pasa a una cola de
  trabajo; la captura reducida y aplicación del resultado siguen en la interfaz.
  Se descarta el resultado si la confirmación ya se cerró.

## Compilación y tamaño

El workflow independiente `ui-beta-debug.yml` usa ahora
`-PflexyPerformanceBuild=true`. Conserva la firma de prueba, pero desactiva la
depuración Java/JNI, selecciona CMake Release y evita los monitores de diagnóstico
de la compilación debug. El perfil debug normal y los controles de la beta
oficial permanecen disponibles.

`tools/apk_size_report.py` informa bytes del APK y contribuciones comprimidas y
sin comprimir de bibliotecas nativas, DEX, Python, recursos y otros archivos.
El workflow lo adjunta en `apk-size.jsonl`. No se han eliminado bibliotecas ni
funcionalidades para reducir el peso.

El aumento comunicado de 92–95 MB a aproximadamente 110 MB no se puede atribuir
a un componente sin comparar ambos APK con la misma arquitectura y perfil.
Tampoco se ha medido aún el tiempo de arranque ni los fotogramas en un teléfono.
Estos cambios corrigen trabajo redundante identificado; no constituyen una
medición de fluidez o tamaño final.

## Validación local

- Suite completa: 207 pruebas aprobadas y 31 omitidas.
- Workflow: actionlint y `git diff --check` sin errores.
- Configuración CMake arm64 del perfil de rendimiento: completada; Release
  seleccionado y opciones de optimización presentes en las reglas nativas.
- La compilación y verificación completa del APK se ejecutan en GitHub Actions.
  El entorno local no tiene acceso a todos los repositorios de dependencias.
