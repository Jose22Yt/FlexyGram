# Instalador privado — iPhone Reference

Perfil independiente del instalador anterior del PR #68. El auxiliar usa `io.github.jose22yt.flexygram.delivery.alpha2.iphone1266`; puede coexistir con el auxiliar antiguo aunque su firma de pruebas sea distinta. La aplicación destino conserva `io.github.jose22yt.flexygram.alpha`, certificado original y versión 1266.

La entrega queda bloqueada mientras APKHash o CipherHash no contengan hashes reales verificados. Solo se aceptan el APK, cifrado y commit fijados en el perfil. Se exige EOF autenticado de age, tar con exactamente APK e informe, inventario de 96 ELF y certificado SHA-256 original explícito. Se rechazan los informes de versiones anteriores y los certificados distintos. Se conserva la política de firmante instalado y prohibición de degradación antes del instalador Android.

El auxiliar no tiene permiso INTERNET ni acceso general al almacenamiento. La identidad age se selecciona mediante Android SAF y solo se procesa en memoria; no se guarda ni se transmite. No incluye la identidad ni la clave de firma de Alpha. La compilación del auxiliar utiliza su propia firma temporal de pruebas.

Archivos de prueba: `FlexyGram-iPhone-Reference-Instalador.apk` y `FlexyGram-iPhone-Reference-1266-arm64.tar.age`. Seleccionar también la identidad age original de la recuperación privada. El destinatario público no permite descifrar. El auxiliar comprueba los archivos antes de ofrecer la actualización; Android vuelve a verificar la firma.

Las pruebas del auxiliar en emulador no certifican el compositor real. Instalación y diseño en Poco X8 Pro / Android 17 siguen pendientes de prueba del propietario.
