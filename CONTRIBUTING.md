# Contribuir a FlexyGram

## Rama de desarrollo

La base activa es `codex/flexygram-beta-glass`. Actualízala antes de preparar un cambio;
`main` y las ramas históricas no son la base de la beta actual.

```sh
git fetch origin
git switch -c mi-cambio origin/codex/flexygram-beta-glass
```

## Preparar una contribución

1. Describe el problema y mantén el cambio limitado a su alcance.
2. Conserva las APIs, preferencias y comportamiento que no formen parte del cambio.
3. Ejecuta las comprobaciones pertinentes e incluye una regresión para los fallos reproducibles.
4. Explica el resultado, las pruebas realizadas y las verificaciones pendientes en dispositivo.
5. Envía la solicitud de cambios a `codex/flexygram-beta-glass` sin reescribir el historial compartido.

La versión y el código de distribución se gestionan en `gradle.properties`. No cambies
la identidad Android ni la configuración de firma como parte de una corrección ajena a ellas.

## Comprobaciones y compilación

Consulta la [guía de compilación](docs/BUILDING.md) y la [guía de pruebas](tests/README.md).
La compilación de referencia se ejecuta en GitHub Actions mediante
`.github/workflows/ui-beta-debug.yml`. Un cambio de documentación no requiere generar una APK;
usa `[skip ci]` en el commit cuando deban omitirse los workflows de push.
Las pruebas aisladas, una compilación integrada y las mediciones en teléfono son verificaciones distintas.

## Organización

- Mantén las guías de uso y arquitectura en `docs/`, las pruebas en `tests/` y las utilidades en `tools/`.
- Los archivos generados, registros locales, cachés y notas personales no se versionan.
- Conserva los originales y manifiestos que las herramientas necesiten para reproducir recursos.
- Retira código o recursos únicamente después de comprobar sus referencias, incluidas las dinámicas.
- Utiliza rutas y comandos reproducibles; evita rutas personales y notas de conversación.

## Licencias y atribuciones

Conserva los avisos originales. Al añadir código, recursos, fuentes o iconos de terceros,
registra autor, fuente, versión o commit y licencia en [CREDITS.md](CREDITS.md), además
de los avisos exigidos en el componente. Resuelve las dudas de procedencia antes de distribuirlo.

## Información privada

No incluyas claves de firma, tokens, configuraciones privadas, sesiones, bases de datos de
cuentas, conversaciones ni capturas personales. Usa archivos locales ignorados o secretos
de CI. Revisa el diff y los adjuntos antes de publicarlos; consulta [SECURITY.md](SECURITY.md).
