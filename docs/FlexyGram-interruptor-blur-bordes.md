# Interruptor de blur y bordes de FlexyGram

Ruta: Ajustes de Telegram → Ahorro de energía → desplegar Animaciones en los
chats → **Blur y bordes FlexyGram**. Se sitúa después de Desenfoque y antes de
las animaciones de escala, donde estaba la opción original Liquid Glass.
Disponible desde Android 12, que admite el blur de fondo usado por esta versión.

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
