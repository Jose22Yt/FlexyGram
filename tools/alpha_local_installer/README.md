# Instalador local independiente de Connected Alpha 2

Perfil separado del instalador de Alpha 1 (PR #60). Paquete auxiliar `io.github.jose22yt.flexygram.delivery.alpha2`. No sustituye la app auxiliar anterior ni modifica o vuelve a firmar FlexyGram.

Selecciona el archivo cifrado de Alpha 2 y el archivo de identidad age original mediante el selector Android. El descifrado ocurre localmente, sin permiso de Internet, sin guardar ni registrar la identidad. El ZIP de recuperación permanece en el teléfono; extrae allí únicamente su archivo de identidad. Nunca envíes el ZIP o la clave privada por chat.

El perfil fija SHA-256 del cifrado y APK, destinatario público original y commit de origen. Exige EOF autenticado de age, tar con exactamente APK e informe, 96 ELF y versión 1262. Antes de cada acceso o instalación vuelve a comprobar APK, identidad y certificado; si ya existe FlexyGram comprueba el mismo firmante y evita degradaciones. El sistema Android hace su propia verificación al actualizar.

Tras verificar, pulsa instalar y acepta **Actualizar**. No desinstales FlexyGram Alpha existente: así la actualización compatible conserva sus datos y sesión. El informe puede guardarse desde la interfaz. “Borrar archivos locales” elimina los resultados privados del auxiliar. No tiene acceso a datos de Telegram.

Las pruebas Go usan identidades desechables solo como fixtures. La instrumentación prueba únicamente el auxiliar en API 35 x86_64; no acredita la barra compacta ni el rendimiento de Alpha 2 en el Poco. El APK auxiliar se firma con una clave efímera propia de CI; nunca consume credenciales de firma de Alpha.
