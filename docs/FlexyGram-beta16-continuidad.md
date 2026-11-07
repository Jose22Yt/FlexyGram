# Continuidad de desarrollo y preparación de beta.16

Ruta principal: `/workspace/FlexyGram-adaptive-bubbles`.
Rama de desarrollo: `codex/flexygram-codex2-mejoras-20261106-v2`.

Las correcciones de pantalla principal, cabecera de chat, iconos y launcher están conservadas en el commit `e6e21c2b9` y se integran con los cinco commits de `codex/flexygram-beta-glass` hasta `6e8e7a3ae715a9f2104b7b107e47fd93b59d35f3`. Se conservan los valores iniciales nativos de esa rama. La siguiente revisión es **1.0.0-beta.16 (1305)**, superior a beta.15.

No se modifica ni se fuerza la rama `codex/flexygram-beta-glass`. La clave Android, el pin público registrado y los validadores de posesión privada permanecen intactos. El verificador de manifiesto recibe explícitamente el alias Glossy esperado en Beta; su comportamiento predeterminado para Alpha se conserva.

## Compilación oficial

El lanzador oficial de `main` requiere un SHA de código inmutable con revisión independiente y aprobación del entorno `flexygram-beta`. Las credenciales se utilizan dentro del runner y no se extraen de GitHub.

La actualización del lanzador se prepara en una rama de infraestructura separada. Debe conservar la protección de `main`, la revisión independiente sobre el SHA exacto, `prevent_self_review`, `can_admins_bypass=false`, el entorno restringido a `main`, el pin de firma y la entrega cifrada. El lanzador no puede firmar esta revisión hasta que se integre esa actualización revisada y se concedan las aprobaciones requeridas.

La identidad de recepción age permanece fuera del repositorio. Solo se publica su destinatario público cuando hace falta configurar la entrega. La integración actual puede consultar el repositorio y las ejecuciones de Actions, pero devuelve HTTP 403 para las API de secretos y variables del entorno; no debe confundirse la autorización del propietario con el alcance efectivo de esa integración.

Las pruebas host y la validación de recursos no equivalen a una APK firmada ni a una prueba en un dispositivo. El hash y la verificación de la APK solo se comunicarán cuando exista un artefacto real de esta revisión.
