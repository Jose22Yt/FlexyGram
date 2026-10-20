# Work — integración PR22 revalidada, 20 de octubre de 2026

FlexyGram, creado y dirigido por @Lukhou23. Al comenzar se verificaron PR17
`c7302da16082a30f39d8ef41886427cbf1edbe6c` y PR22
`0ffcf81bd1aaba2512ff1b0ef09472e612c45d1c`. Se preparó una copia temporal y se
ejecutaron318 pruebas principales y35 de laboratorio en normal y `-O`.

Antes de publicar, el propietario incorporó concurrentemente la integración revisada
en `19200e843cc9bf31c27a99e7b6775494627b131e`, con un preflight más estricto y un
gate combinado. Se conserva íntegramente ese commit; no se sobrescribe con la copia
temporal ni se duplican los cambios. La rama PR22 permanece separada.

Se recuperó un checkout limpio de19200e8 y se ejecutó su `run_combined_gate.py` real
con Python3.11.17 y JDK21.0.10, fuentes PR20/21 fijadas por hash:

- **367/367 métodos distintos PASS** normal:318 nativos y49 readiness.
- **367/367 PASS** `-O`, los mismos casos, cero fallos/errores/omisiones.
- Índices de IDs y hashes de fuente capturados por el gate, sin duplicados.

La incompatibilidad del marcador AVD `<temp>` y el desacuerdo sobre rutas de datos/AVD
ya están corregidos en19200e8 y se verifican en sus regresiones. Los banners ADB no
contaminan get-state, los puertos fuera de rango se rechazan y los dos consumidores
utilizan el controlador corregido. No se añade otro ejecutor ni se amplían prefijos
de alcance. Los hashes exactos de los nuevos archivos son los registrados por19200e8.

No hay host alternativo autorizado accesible: el host actual mantiene capacidades0,
seccomp y ausencia de KVM/TUN/Docker/Podman. No se repiten las sondas ya denegadas ni
se descargan imágenes. Android no ejecutado. Se continúa el trabajo de cliente en
`development/beta-offline-foundation`, separado de esta rama de seguridad.

Este commit añade solo documentación y recibos. Main/develop intactas, PR2 abierto,
PR17 DRAFT, sin claves/firma/instalación/servicios/Production/Actions/Paso4.

[Recibos originales de esta ejecución](evidence-work-pr22-verified/).
