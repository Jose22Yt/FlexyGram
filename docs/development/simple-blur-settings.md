# Ajustes simples de blur y borde

Sustituye el editor experimental `a66f36e6b9`. Se elimina la vista previa y se
cancela la ampliación a perfiles y otras superficies nuevas.

## Resultado

La entrada **Blur y bordes** conserva un interruptor y cuatro controles:
intensidad de desenfoque, intensidad del borde, grosor y tipo de contorno
(predeterminado, sólido o desactivado). No hay escenas ficticias, selector de
zonas, paleta de colores, preajustes ni modos de tema para vista previa.

Los archivos de perfiles, acciones, pestañas, cabeceras y pintor de pantalla
principal vuelven exactamente a la beta `1c323bf54c`, anterior al experimento.
Las ubicaciones originales del material siguen siendo las de esa beta. También
se recuperan sus colores, sombras y proporción entre borde superior/inferior.

Los valores del experimento cancelado dejan de intervenir. Los nuevos ajustes
simples usan claves separadas: por defecto radio 40, borde 70 %, grosor 0,8 dp y
opacidad interna 42, como el material anterior. La transparencia no es un control
visible. El tipo de contorno utiliza el ajuste nativo existente, compartido con
la sección anterior de efectos de brillo; no existe otro selector incompatible.

## Rendimiento

Se conserva la instantánea inmutable en memoria y la captura nativa compartida.
No hay buffers, capturas ni callbacks de vista previa. Arrastrar solo actualiza
el valor local y su etiqueta; se guarda una vez al soltar y se actualizan las
pantallas anteriores al salir. Radio cero no crea un RenderEffect de desenfoque.
Se mantienen los límites de radio/grosor y las restricciones anteriores de
LiteMode, ahorro de energía, tema y legibilidad.

## Verificación

Suite local completa: **247 pruebas aprobadas y 32 omitidas**, sin fallos.

Las pruebas comparan byte a byte los archivos de las zonas canceladas con
`1c323bf54c`; ejecutan la configuración real, caché, guardado, límites y efectos
retenidos en JVM. Se comprueban los recursos de inglés, español y ruso con AAPT2.

```sh
JAVA_HOME=/ruta/al/jdk ANDROID_HOME=/ruta/al/sdk \
  python3 tools/glass/check_simple_settings.py
```

La comprobación anterior usa Android API 37 y dobles de servicios del proyecto.
La compilación y firma de la APK de pruebas se validan por separado mediante el
workflow ARM64 existente de GitHub Actions. No se modifica la firma oficial.
La revisión visual y de fluidez real sigue requiriendo pruebas en dispositivo.
