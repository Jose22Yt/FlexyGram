# Instalador offline — Signature Home 2

Perfil independiente basado en PR77, compatible únicamente con la entrega1268 del HEAD cb2c98234aa7e88550853d54132e52d629b2674f. Mantiene el paquete y certificado originales de Alpha para actualizar sin borrar su sesión. El auxiliar tiene paquete propio para coexistir con los anteriores.

Instala FlexyGram-SignatureHome2-Instalador.apk; selecciona FlexyGram-SignatureHome2-ARM64.tar.age y la identidad age original local, pulsa Descifrar y comprobar y después Actualizar. No se solicita el ZIP privado por red. No tiene permiso INTERNET ni acceso general al almacenamiento.

Se conservan los controles originales: hash del cifrado, destinatario original, autenticación age hasta EOF, tar estricto, hash de APK, informe,96 ELF, paquete, versión y certificado. Rechaza firmas incompatibles y versiones posteriores instaladas. Los pins se fijan después de verificar la compilación real; el gate bloquea la construcción si faltan. Los ensayos utilizan identidades desechables exclusivas de pruebas.

La prueba física de actualización y fluidez en Poco Android17 sigue pendiente; un emulador del auxiliar no la sustituye. No publiques la APK Alpha descifrada ni la identidad privada.
