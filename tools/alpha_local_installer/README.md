# Instalador privado — Alpha 2 integrada

Perfil independiente del instalador anterior del PR #75. El auxiliar usa `io.github.jose22yt.flexygram.delivery.alpha2.integrated1267`; puede coexistir con el auxiliar antiguo aunque su firma de pruebas sea distinta. La aplicación destino conserva `io.github.jose22yt.flexygram.alpha`, certificado original y versión 1267.

La entrega queda bloqueada mientras APKHash o CipherHash no contengan hashes reales verificados. Solo se aceptan el APK, cifrado y commit fijados en el perfil. Se exige EOF autenticado de age, tar con exactamente APK e informe, inventario de 96 ELF y certificado SHA-256 original explícito. Se rechazan los informes de versiones anteriores y los certificados distintos. Se conserva la política de firmante instalado y prohibición de degradación antes del instalador Android.

El auxiliar no tiene permiso INTERNET ni acceso general al almacenamiento. La identidad age se selecciona mediante Android SAF y solo se procesa en memoria; no se guarda ni se transmite. No incluye la identidad ni la clave de firma de Alpha. La compilación del auxiliar utiliza su propia firma temporal de pruebas.

Archivos de prueba: `FlexyGram-Alpha2-Integrada-Instalador.apk` y `FlexyGram-Alpha2-Integrada-1267-arm64.tar.age`. Seleccionar también la identidad age original de la recuperación privada. El destinatario público no permite descifrar. El auxiliar comprueba los archivos antes de ofrecer la actualización; Android vuelve a verificar la firma.

Las pruebas del auxiliar en emulador no certifican el compositor real. Instalación y diseño en Poco X8 Pro / Android 17 siguen pendientes de prueba del propietario.

Entrega1267 compilada y verificada en Actions40060346675. La barra aprobada del PR74 permanece idéntica.

SHA256 APK `48abf0f8a32fb36b28de87f17955df922ba3ca643c4a2d35dbb0c86c543ac67c`; cifrado `ae9b7bbbc22757096cd33e78bf0d726d4865581f1fdae12fd915935bf1585828`.
