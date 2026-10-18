# GitHub, workflows y requisitos del siguiente paso

[Índice](README.md). Estado verificado el 18 de octubre de 2026.

## Ramas y protección administrativa

Al comenzar, `main` y `develop` apuntaban a `db1bea24b7b705de33f8ff8c8e174011c153cac7`, ambas `protected=false` en la API. La UI de Branches también indicaba que no había reglas clásicas.

Con la autorización del PASO 2 se creó una regla clásica para el patrón exacto **main**. La UI confirmó “Branch protection rule created”; se reabrió la edición para verificar persistencia. La API de ramas pasó a indicar `protected=true` para main y `false` para develop.

| Control de main | Estado guardado |
| --- | --- |
| Require a pull request before merging | Activado |
| Require approvals | Desactivado; no exige segundo revisor |
| Require conversation resolution | Activado |
| Do not allow bypassing the above settings | Activado; incluye administradores |
| Allow force pushes | Desactivado |
| Allow deletions | Desactivado |
| Require status checks / deployments / signed commits / linear history | No exigidos |
| Lock branch | Desactivado |

Se evitó exigir CI inexistente o una segunda persona, que podría impedir el trabajo del propietario. `develop` permanece sin protección en esta etapa: la petición autorizaba configurar protección básica de main. Las aportaciones de la auditoría se proponen igualmente por rama documental y PR a develop; no se integran automáticamente. El administrador conserva capacidad de editar políticas desde Settings; una regla no impide que el propietario cambie la configuración deliberadamente.

Evidencia verificable: [ramas API](https://api.github.com/repos/Jose22Yt/FlexyGram/branches), [Settings/Branches](https://github.com/Jose22Yt/FlexyGram/settings/branches). La configuración administrativa no forma parte del diff Git.

## Estado real de Actions

Se inspeccionó directamente [Settings/Actions](https://github.com/Jose22Yt/FlexyGram/settings/actions): **Disable actions seleccionado**. No se cambió ese estado ni se pulsó habilitar workflows. Los permisos predeterminados visibles eran lectura de contenidos/packages y sin permiso para crear/aprobar PR; un workflow puede declarar permisos diferentes si algún día se habilita.

La [API de runs](https://api.github.com/repos/Jose22Yt/FlexyGram/actions/runs) mostraba cero ejecuciones al inicio de la revisión y se vuelve a consultar al verificar la entrega documental. Cero runs por sí solo no demuestra desactivación: la evidencia de desactivación es el control administrativo.

## Workflows heredados inspeccionados, nunca ejecutados

| Archivo | Disparador declarado | Capacidad relevante / riesgo pendiente |
| --- | --- | --- |
| `release.yml` | Push a main y workflow_dispatch; `publish` predeterminado true; ignora Markdown | Construye universal, restaura firma si existe, publica GitHub prerelease, elimina antiguas `ci-*` después de conservar cinco y puede enviar APK a Telegram. Job con contents:write |
| `pr.yml` | pull_request opened/reopened/synchronize; ignora Markdown y XML | Construye debug ARM64; no declara permissions explícitos, hereda defaults. Exporta LOCAL_PROPERTIES en script y usa un sed que no coincide exactamente con el ternario actual de firma |
| `staging.yml` | Push a `dev`, no `develop`, y manual | Staging universal y artefacto; contents:read. Input `upload` declarado, sin uso visible para condicionar upload-artifact |
| `canary.yml` | Push a canary y manual | Staging universal y artefacto; contents:read. Nombre del artefacto y paso dice staging; input upload no controla el paso visible |

Referencias: [.github/workflows/release.yml:L1](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/release.yml#L1), [.github/workflows/pr.yml:L1](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/pr.yml#L1), [.github/workflows/staging.yml:L1](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/staging.yml#L1), [.github/workflows/canary.yml:L1](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/canary.yml#L1).

### Hallazgos de automatización

- **Alta, hecho + riesgo latente:** release tiene publicación y borrado automático, no solo construcción. La descripción del input habla de Telegram, pero también condiciona publicación GitHub. El patrón `ci-*` es el filtro del borrado; no debe activarse sin decidir política de retención. [.github/workflows/release.yml:L117](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/release.yml#L117).
- **Alta, hecho:** `send_apk.py` usa Pyrogram con credenciales TG_*, selecciona una APK y envía un documento. No se ejecutó ni se envió mensaje alguno. [.github/scripts/send_apk.py:L63](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/scripts/send_apk.py#L63).
- **Alta, riesgo:** interpolar secrets.LOCAL_PROPERTIES dentro de un bloque shell no es equivalente a pasarlo exclusivamente por env estructurado. Revisar límites de confianza y exposición antes de habilitar. Los valores reales no se leyeron. [.github/workflows/pr.yml:L66](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/pr.yml#L66), [.github/workflows/release.yml:L95](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/release.yml#L95).
- **Media, hecho:** actions referenciadas mediante tags; paquetes pip sin versión en app y en envío Telegram; checkout inicializa submódulos recursivos. Reproducibilidad y confianza externa requieren revisión. No se comprobó disponibilidad de cada tag ni integridad de artefactos. [.github/workflows/release.yml:L39](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/release.yml#L39), [.github/workflows/release.yml:L141](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/release.yml#L141), [TMessagesProj/build.gradle:L140](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L140).
- **Media, hecho:** CMake no aparece instalado de forma explícita en esos workflows; Gradle declara un selector abierto. La resolución real del entorno queda pendiente, no se declara una CI rota. [TMessagesProj/build.gradle:L217](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L217).
- **Media, hecho:** excluir XML de PR puede dejar fuera cambios de UI/manifest; un futuro CI debería validar esos cambios. El sed de firma de PR tampoco garantiza quitar la firma release actual. [.github/workflows/pr.yml:L8](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/pr.yml#L8), [.github/workflows/pr.yml:L68](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/pr.yml#L68).
- **Media, hecho:** todas las rutas hacen checkout shallow. Para una construcción puede bastar, pero no acredita análisis completo del historial ni procedencia de prebuilts.

No se habilitó ningún workflow, no se modificó YAML ni scripts y no se cargaron secretos. La auditoría no certifica los workflows como seguros: la recomendación es mantenerlos desactivados hasta una revisión específica previa a CI/publicación.

## Requisitos concretos propuestos para PASO 3

Este listado es una propuesta para autorización posterior, no trabajo iniciado.

1. **Aprobar esta auditoría y revisar su PR documental.** Registrar el SHA aprobado; conservar main/develop funcionalmente iguales a la base hasta decidir cambios.
2. **Cerrar requisitos del entorno:** comprobar disponibilidad y compatibilidad de JDK 21, Gradle 9.7.1, AGP 9.3.1, SDK 37, Build Tools 36.0.0, NDK 27.2.12479018, CMake y Python 3.11/Chaquopy. Registrar versiones reales y cualquier divergencia, sin actualizaciones silenciosas.
3. **Revisar fuentes faltantes:** inicializar solo submódulos autorizados con SHA fijo, comprobar core_settings/common-ktx y build runtime Chaquopy; revisar scripts antes de ejecutarlos.
4. **Definir construcción de referencia:** variante ARM64 sin cambios funcionales; resolver configuración de prueba/firma/servicios. No distribuir como versión final ni usar un keystore temporal para una línea pública permanente.
5. **Definir acceso y datos de prueba del Poco:** confirmar versión de sistema/API/ABI, refresh real, tamaño de página, navegación, batería y temperatura; usar datos/cuenta de prueba adecuados.
6. **Aprobar matriz y criterios:** caché caliente/fría, grupos/canales/bots/foros, apertura/back/preview/reacciones/teclado/oscuro, plugins controlados y escalas del sistema. Definir cómo almacenar resultados y capturas sin datos personales.
7. **Separar compilación de medición:** decidir explícitamente si Paso 3 solo prepara/verifica entorno o también autoriza una primera APK de referencia y ensayos. El PASO 2 no concede esa autorización.
8. **Mantener CI desactivado por ahora:** una autorización de construcción local no es autorización de publicación automática, Telegram o borrado de releases.

Salidas que deberá producir la etapa que se autorice: manifiesto del entorno/submódulos, registro de construcción si se permite, identidad verificable del artefacto si se genera, errores íntegros relevantes, y un plan de medición aprobado. Optimizar solo después de tener resultados reproducibles que identifiquen causa y magnitud.

## Condiciones de cierre del PASO 2

La rama documental debe contener únicamente archivos bajo `docs/audit-step-2/`; el PR debe dirigirse a develop y permanecer abierto para revisión. Main/develop no reciben código ni merge durante esta entrega. Comprobar diff, SHA de ramas, estado de protección y cero runs al finalizar. Identidad @Lukhou23 y GPL-3.0 se mantienen.
