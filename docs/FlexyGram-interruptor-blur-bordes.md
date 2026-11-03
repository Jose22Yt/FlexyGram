# Interruptor de blur y bordes de FlexyGram

Ruta actual: **FlexyGram → Universal → Blur y bordes**. Se retiró el control
personalizado de Ahorro de energía de Telegram. La pantalla tiene únicamente
el interruptor maestro y los controles existentes de opacidad e intensidad del
borde, agrupados en una tarjeta. El acabado se aplica automáticamente a todas
las superficies compatibles; no hay selectores de zonas ni botón Aplicar.

Los sliders conservan los valores guardados y activan el material personalizado
al editarlos. Sus cambios se guardan durante la interacción y las pantallas
abiertas se reconstruyen al salir de la sección. Entrar sin cambiar valores
conserva el acabado actual. Las exclusiones antiguas por superficie se ignoran;
el ahorro de energía y el desenfoque nativo siguen respetándose.

- Interruptor maestro persistente en `FlexyBackdropGlassEnabled`, inicialmente
  activado para conservar la presentación de la beta ya entregada.
- Activado: habilita el material actual de FlexyGram, sujeto al desenfoque nativo,
  la capacidad del dispositivo y el ahorro de energía. No reactiva la refracción.
- Desactivado: anula el blur de chat, oculta contornos y reflejos y fuerza una
  superficie opaca en los drawables retenidos, evitando reproducir sus capturas
  desenfocadas anteriores. Las rutas de reserva de cabecera, carpetas y compositor
  tampoco pintan sus bordes decorativos.
- No modifica la selección guardada de contorno, opacidad ni personalización
  Universal. Al activar de nuevo se recuperan esos valores.
- El cambio avisa a los drawables y a las superficies abiertas mediante los
  listeners existentes. Las fuentes de conversación se conservan incluso si se
  abrió el chat con el interruptor apagado, para admitir una activación posterior.
- El interruptor original de desenfoque de Telegram se conserva y sigue siendo
  una condición del renderizado. El nuevo interruptor controla conjuntamente el
  material y los contornos añadidos por FlexyGram.

Validación local: 209 pruebas aprobadas y 31 omitidas; sintaxis Java, recursos
XML y diff correctos. La prueba JVM nueva verifica el estado inicial, apagado,
persistencia tras recargar la caché, idempotencia y restauración de los tres
estilos de borde sin alterar su preferencia guardada. Las comprobaciones de
compatibilidad conservan los renderizadores previos, admitiendo únicamente las
nuevas condiciones del interruptor. La validación visual en dispositivo queda
pendiente del APK que produce el workflow ARM64 al publicar este cambio.


Validación de la reorganización: 211 pruebas aprobadas y 31 omitidas; Java, XML
y diff válidos. Se amplió la prueba JVM del material para comprobar que los
valores antiguos de zonas (incluido cero) no desactivan superficies compatibles.
La comparación visual del nuevo diseño en teléfono queda pendiente del APK.
