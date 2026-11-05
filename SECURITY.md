# Seguridad

## Comunicar un problema de forma privada

Si detectas una vulnerabilidad, una clave expuesta o información de una cuenta, utiliza **Security → Advisories → Report a vulnerability** si GitHub ofrece esa opción en este repositorio. Si no está disponible, contacta de forma privada con el [responsable del proyecto](https://t.me/Lukhou23) para acordar un canal de envío. No publiques el secreto en Issues, comentarios, capturas o registros de Actions.

Indica la versión o commit afectado, el impacto y pasos mínimos para reproducirlo con datos de prueba. No adjuntes sesiones, mensajes personales, números de teléfono ni pruebas que accedan a cuentas ajenas.

## Credenciales y configuraciones locales

Guarda claves de firma, contraseñas y tokens en archivos locales ignorados o secretos del sistema de integración. Usa tus propias credenciales de servicios. Los archivos ignorados que ya estén versionados o publicados en el historial siguen siendo accesibles: `.gitignore` no los retira.

Si una credencial real fue publicada, su propietario debe revocarla o rotarla en el servicio correspondiente. Retirarla de una nueva versión del archivo no invalida las copias ni el historial. La limpieza histórica debe coordinarse por separado para no sobrescribir trabajo de otros colaboradores.

Los certificados y claves de fixtures criptográficos públicos no son credenciales de producción. Deben conservarse junto con sus pruebas y avisos de origen.

## Registros y capturas

Antes de compartir material, elimina tokens, cookies, claves, mensajes privados, datos de cuenta e identificadores de personas. Prefiere datos ficticios y registros mínimos. Si no puedes depurarlos con seguridad, describe el problema sin subirlos.

No se establece un plazo de respuesta o una versión segura sin una confirmación del equipo.
