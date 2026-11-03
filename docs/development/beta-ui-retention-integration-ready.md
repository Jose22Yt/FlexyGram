# Integración preparada para la próxima APK beta

Se integra `fix/current-beta-ui-retention` (`77a1e767c8cdbb5c01043133178d6cc08d45268d`) en `codex/flexygram-beta-glass`, sobre `6342e1d4603b41fc37f6a34d02475edf6205ec83`. La integración no presentó conflictos de Git y conserva los cambios anteriores de navegación adaptable, búsqueda, contraste claro/oscuro, tamaños del compositor, vista previa de mensajes y arranque nativo.

Se incorporan los ajustes compactos y sus iconos adaptables, contador de mensajes por carpeta con contraste, herramientas de IA/editor en el compositor, blur/bordes de canales, reutilización de buffers y conservación ordenada del historial de AyuMoments. También se incorporan las correcciones de cancelación de transiciones de reacciones y la eliminación de la llamada explícita a GC al cerrar el selector.

La revisión añadió una corrección: el botón de expandir el editor ahora actualiza tanto el color del icono como su selector al recibir cambios de tema. Antes solo recibía los colores al construirse, por lo que podía conservar un color del modo anterior. Se mantuvieron sus dimensiones y posición.

## Verificación realizada en este entorno

- Con JDK 21 en `PATH`, `python -m pytest tests/ -q -p no:cacheprovider`: **229 aprobadas, 31 omitidas**. Se ejecutaron los casos Java de las mejoras importadas, además de las pruebas de la beta anterior.
- Las pruebas cubren cálculo por carpeta y contraste del contador, reglas de las herramientas del compositor, medición sin reinicios de animación, rutas de blur nativo y fallback para canales, dimensiones/reutilización de buffers y orden de conservación frente al borrado.
- Prueba adicional ejecutando el método real que actualiza el botón del editor con distintos colores de tema y comprobando su conexión al refresco de colores.
- Sintaxis Java de todos los archivos integrados revisada con tree-sitter; `git diff --check` sin errores.
- AAPT2 compiló los recursos XML nuevos/modificados en un archivo de recursos, sin enlazar ni generar una APK.
- `Settings2Cell`, `CompactSettingsTextCell` y `SettingsIcons` compilaron contra Android API 37 con dependencias de aplicación mínimas.

## Estado

El código queda listo para iniciar la compilación beta cuando el usuario lo indique. El commit de integración incluye `[skip actions]` para publicar las fuentes sin disparar el workflow automático de compilación. No se modifican los workflows ni la configuración de firma.

Esta preparación no equivale a una compilación Android completa ni garantiza ausencia de defectos visuales en un dispositivo. Queda validar la APK resultante en modo claro/oscuro, escritura larga y teclado, expansión y herramientas del editor, canales/contactos, navegación y búsqueda, reacciones e historial conservado. No se afirma una mejora medida de FPS ni una verificación real de Room o del IME.
