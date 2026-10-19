# P0.4a — Arquitectura de identidad propia (propuesta)

Fecha: 2026-10-19. FlexyGram 1.0, creado y dirigido por **@Lukhou23**. Estado: diseño pendiente de aprobación; no es implementación autenticable ni Paso 4.

## Integración autorizada y trazabilidad

PR #13 se verificó abierto, dirigido a develop y con head exacto `86226a55d59c2bac5a85516a1ab4d97a67801961`, sin cambios adicionales. Se marcó listo y se fusionó exclusivamente en develop mediante merge: **`781b18be703809898ac0478c6239d53216ebd736`**. Esta rama documental nace de esa integración. Main no se modifica y PR #2 se conserva abierto.

Las evidencias de P0.3g permanecen en [su carpeta original](../security-p03g/evidence/). Se verificaron los 11 hashes de fuentes congeladas contra el código revisado y se indexaron los hashes de los documentos/logs en [evidence/pr13-evidence-hashes.json](evidence/pr13-evidence-hashes.json). Los seis logs finales registran 26+27+4+14+12+10 = **93 pruebas**, sin fallos ni omisiones. La compilación histórica completa ARM64 con JNI y Chaquopy terminó correctamente en 8m39s, 252 tareas; APK interno SHA-256 `6302ecb37ca15716b5ce56fe1039845841454092b35181ffcd35cb82832cd066`. No se repitieron pruebas ni compilación aprobadas. Un commit documental nuevo no representa una nueva compilación. Estos datos NO prueban instalación, ART, arranque, restauración o tráfico Android real.

## Documentos

- [Inventario y puntos que deben separarse](INVENTORY.md).
- [Arquitectura de variantes, credenciales, firma y datos](ARCHITECTURE.md).
- [Compatibilidad API24, API37, JNI/Python y 16 KB](ANDROID-COMPATIBILITY.md).
- [Orden, archivos previstos, pruebas y bloqueo de beta](IMPLEMENTATION-PLAN.md).

Esta entrega añade únicamente documentación. No cambia aplicación, manifiestos, módulos, credenciales, configuración nativa, UI, animaciones, rendimiento, reproductor o actualizador. No activa INTERNET, autenticación, push, Actions ni servicios. No instala ni distribuye APK. Las decisiones de identidad y operación descritas son propuestas; no se han reservado identificadores ni obtenido cuentas/credenciales.
