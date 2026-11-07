# Activación revisada de la compilación oficial beta.16

Fuente: PR #180, commit `6ea76c7082fd51d51fa51ebf03a572a192eda86a`, versión 1.0.0-beta.16 (1305). Incluye los cinco commits recientes de la rama beta y las correcciones de interfaz. La rama beta y main no se sobrescriben.

Esta propuesta cambia únicamente el código de control de Actions y su manifiesto. El código de la aplicación está en el commit fuente separado. Se conservan el certificado registrado, la identidad del entorno, su revisión independiente, la prevención de autoaprobación, la prohibición de bypass administrativo y la restricción a main. La revisión de código debe aprobar exactamente el SHA del PR #180; no sirve una aprobación sobre una revisión anterior.

Antes de ejecutar la nueva compilación:

1. Obtener la aprobación independiente del PR #180 por el revisor ya configurado `dc6764071-wq`.
2. Revisar e integrar esta propuesta de infraestructura en main mediante sus reglas existentes.
3. Establecer la variable del entorno `flexygram-beta` llamada `FLEXYGRAM_BETA_AGE_RECIPIENT` al destinatario público de `policy.json`. No es una contraseña. La integración actual recibe HTTP 403 para consultar/modificar esta variable, por lo que este paso debe hacerlo el propietario con acceso a esa configuración.
4. Ejecutar `Official Beta private ARM64` desde main con `mode=build` y aprobar el despliegue con el revisor independiente configurado. No se aprueba el propio despliegue ni se relajan protecciones.

El artefacto se cifra para la identidad age de recepción conservada fuera del repositorio en el entorno de desarrollo actual. GitHub no entrega sus secretos almacenados por API y esta propuesta no intenta exportarlos. No se muestran entradas privadas ni se genera otra firma Android.

Se elimina la modificación histórica del verificador después de compilar: el commit fuente ya reconoce explícitamente el alias Glossy en Beta. La fuente firmada y su verificación permanecen ligadas al manifiesto revisado.

Los tests de infraestructura usan credenciales/APK sintéticos y una prueba real de cifrado age con una identidad desechable de prueba, que no es una firma Android. No acreditan una APK real ni una instalación.

Verificación de la propuesta: 16 pruebas de infraestructura aprobadas (incluyen rechazo de deriva de protecciones, revisión de otro SHA o revisor, rechazo de firmas incorrectas y round-trip real de age sobre datos sintéticos), actionlint 1.7.12 con checksum fijado sin errores. La consulta actual de las protecciones pasa; la consulta del código nuevo devuelve `SOURCE_INDEPENDENT_APPROVAL_PENDING`. La suite integrada del cliente pasó 342 pruebas con 33 omisiones y las 15 pruebas enfocadas pasaron. No existe una APK oficial beta.16 construida por esta propuesta.
