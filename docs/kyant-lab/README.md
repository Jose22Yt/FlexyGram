# FlexyGram Glass Lab: experimento separado

Base antigua: `9b305e3ee7ee16097576d60af07f6ed9f105de9c` (beta.58).
Rama: `codex/flexygram-legacy-kyant-glass-test`.
Paquete: `com.flexygram.messenger.kyantlab`; nombre: FlexyGram Glass Lab.
No modifica ni reemplaza `com.flexygram.messenger.nativebaseline`.

La base principal optimizada es `d50640dec57ee26c957b2b0342fe47cf4006acf5`,
etiqueta remota `flexygram-optimized-base-beta60`. Ese árbol no se modifica
para implementar este experimento. La base antigua conserva sus otras funciones;
esta APK no sirve para atribuir al nuevo material cualquier diferencia frente a
la base optimizada sin controlar el resto de ajustes y carga de cada app.

Se usa `io.github.kyant0:backdrop:2.0.1` y el componente LiquidBottomTabs real
del catálogo AndroidLiquidGlass-kmp subido por el usuario. Los seis archivos del
componente y sus helpers conservan la óptica, constantes y gestos originales;
solo cambian los paquetes. SHA256 originales en third_party/kyant-backdrop,
con la licencia Apache2.0 y avisos. No se sustituye el shader global de Telegram
ni se instala debajo del dock nuevo. Las otras superficies antiguas permanecen.

KyantDockView aloja el componente Compose sobre las vistas originales de los
botones, que conservan iconos, badges, cuentas y callbacks nativos. La selección
usa el componente original. El long press nativo se conserva en el puente de
entrada y cancela la secuencia Compose cuando abre el menú. El componente se
recrea cuando cambia el conjunto de destinos para que el rango de arrastre sea válido.
Un solo destino vuelve a la barra nativa simple, evitando el rango cero del demo.

KyantBackdropSource registra únicamente la página nativa, nunca la barra,
en un RenderNode recortado al área del dock con margen óptico. Reutiliza la
captura hasta cambiar contenido/geometría; contempla matrices de transformación.
No usa capturas Bitmap, PixelCopy ni lecturas de GPU a CPU. Los cambios se
agrupan con un callback de frame, sin ticker propio. Se ignoran invalidaciones
causadas por la propia captura o el dibujo manual del icono para evitar realimentación.
La composición se dispone al desprenderse; las capas y callbacks se liberan.
La rama de Kyant queda fuera de la instrumentación antigua de FastMotion.

Requiere Android13/API33 y aceleración hardware para este material completo.
La barra simple se conserva para versiones anteriores y ahorro de energía.
El material usa la cápsula de 64dp original de Kyant; los controles antiguos de
geometría del dock no sustituyen sus shaders ni sus constantes ópticas.
No hay mediciones en un teléfono ni prueba de equivalencia visual píxel a píxel.
La compilación JVM/Android y las comprobaciones de aislamiento son necesarias;
la aceptación de interacción/renderizado real queda para la prueba de la APK.

Validación previa al ensamblado: 517 pruebas aprobadas, 41 omitidas por las
capacidades locales disponibles. Tres contratos nuevos cubren identidad separada,
procedencia del componente original y reutilización del RenderNode (10.000
redibujados estables producen una sola captura; revisiones/geometría la invalidan).
La compilación aislada usa las dependencias reales y dobles explícitos únicamente
para las APIs anfitrionas de FlexyGram; no es una prueba de interfaz en dispositivo.
El helper Android de espera de frame sustituye el expect/actual del catálogo KMP.
