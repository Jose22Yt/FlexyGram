# Superficies nativas de conversación

Referencia de la integración histórica de las superficies Glass de Telegram en la
cabecera y el compositor de FlexyGram.

La disponibilidad depende de `LiteMode.FLAG_LIQUID_GLASS` y de los recursos de blur
nativos. La cabecera reutiliza los drawables existentes de Telegram. El compositor
compacto utiliza una unión de contornos y un único pase nativo compartido para sus
superficies, con geometría y objetos de dibujo reutilizados.

Cuando el motor no está disponible, está desactivado o el compositor atraviesa un
estado incompatible, se conserva el fondo nativo de reserva y sus superficies táctiles.
Los contratos de esta carpeta corresponden a las revisiones que documentan; no prueban
el rendimiento físico de la versión actual.
