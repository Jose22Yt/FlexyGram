# Contribuir a FlexyGram

Gracias por ayudar a mejorar el proyecto. Antes de empezar, indica el problema, la rama y el commit de base: `main` puede diferir de la beta actual.

## Preparar un cambio

1. Crea una rama propia desde la base acordada.
2. Mantén el cambio pequeño y conserva APIs, preferencias y comportamiento fuera de su alcance.
3. Añade una prueba de regresión cuando corrijas un fallo reproducible y ejecuta las comprobaciones pertinentes.
4. Explica qué cambia, cómo se comprobó y qué queda pendiente de validar en dispositivo.
5. Abre una solicitud de cambios sin reescribir el historial compartido.

Consulta la [guía de compilación](docs/BUILDING.md). Los cambios de documentación no necesitan generar una APK. Los resultados de pruebas aisladas deben distinguirse de una compilación completa y de las mediciones en teléfono.

## Licencias y atribuciones

Conserva los avisos originales. Al añadir código, recursos, fuentes o iconos de terceros, registra autor, fuente, versión o commit y licencia en [CREDITS.md](CREDITS.md), además de los avisos exigidos en el componente. Si su licencia o procedencia no está clara, resuélvela antes de distribuirlo.

## Información que no debe publicarse

No incluyas claves de firma, tokens, configuraciones privadas, sesiones, bases de datos de cuentas, conversaciones ni capturas personales. Revisa el diff y los adjuntos antes de publicarlos. Los registros deben estar depurados; consulta [SECURITY.md](SECURITY.md).
