# Primera Beta oficial: infraestructura privada

Estado inicial: **BLOQUEADA para secretos reales y compilación firmada** hasta verificar el entorno. Código fuente fijo: PR #141, `aeb6b5fc01f6332ab82194e311b52a19d702a81e`. No hay APK nueva ni aceptación en Poco. Paquete `com.flexygram.messenger`, nombre `FlexyGram Beta`, versión `1.0.0-beta.1`, código `1290`, alias `flexygram-release`, SHA-256 `5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c`.

## Ruta de revisión y activación

1. Revisar el PR apilado sobre PR141: solo infraestructura y una extensión exacta del auditor histórico; ninguna función Android ni identidad cambia. La compilación sigue usando el commit PR141 íntegro, no la punta de esta rama.
2. Revisar por separado el PR de activación contra `main`. Solo traslada `.github/beta/*` y los dos workflows `beta-private*.yml`; **no fusionar toda la integración en main para registrar el workflow**. No mezclar cambios de aplicación en este PR. Estos archivos quedan cubiertos por `paths-ignore: .github/**` del antiguo `release.yml`, que permanece intacto. Verificar nuevamente ese filtro antes de fusionar; otros workflows existentes pueden ejecutar comprobaciones sin firma.
3. No se fusiona ningún PR automáticamente. El propietario debe revisar y fusionar el PR de activación para que GitHub registre `workflow_dispatch` en la rama predeterminada. El workflow rechaza dispatch desde cualquier referencia distinta de `main`. No hay entrada para SHA/rama, publicación, certificado o variante.
4. Antes de cargar credenciales, crear y comprobar las protecciones de abajo, registrar los controles manuales en `policy.json` mediante otro PR revisado a main, ejecutar `audit` sin secretos y exigir resultado satisfactorio. Conservar el enlace al run de auditoría y a la revisión de controles. Una aprobación del entorno debe comprobar el SHA del lanzador y la fuente fijada.
5. Solo después cargar los siete secretos en el entorno. Ejecutar `build` desde main. Una persona distinta del iniciador aprueba el job del entorno. Al modificar la fuente aprobada o el workflow, se requiere una revisión nueva; no hay sustitución de commit por input.

## Crear y comprobar el entorno, antes de secretos

En `https://github.com/Jose22Yt/FlexyGram/settings/environments`, **New environment**, nombre exacto `flexygram-beta`:

1. Activar **Required reviewers** y elegir uno o varios usuarios individuales de confianza con acceso al repositorio (no equipos). Activar **Prevent self-review**. El iniciador del workflow y quien aprueba el despliegue deben ser personas diferentes. Si solo existe un colaborador, incorporar otro revisor autorizado antes de habilitar la firma; no desactivar este control para desbloquearla.
2. Desactivar **Allow administrators to bypass configured protection rules**. Guardar. Este control y las reglas detalladas de main requieren inspección de la interfaz del propietario: no afirmamos que el API los demuestre.
3. En **Deployment branches and tags**, seleccionar **Selected branches and tags**, añadir únicamente **Branch: main**, sin tags, patrones, otras ramas ni selección genérica de ramas protegidas. Guardar.
4. En protección de `main`, exigir PR con al menos una aprobación, invalidar aprobaciones antiguas al cambiar código y exigir aprobación del último push por otra persona; impedir force push y eliminación, aplicar las reglas también a administradores, sin actores de bypass. Revisar específicamente cambios de `.github/**`. No habilitar la firma si el plan/configuración no permite aplicar estas restricciones.
5. Todavía **no cargar secretos**. Consultar desde una sesión local del propietario autenticada con `gh` (los siguientes GET no leen valores de secretos):

   ```bash
   gh api repos/Jose22Yt/FlexyGram/environments/flexygram-beta
   gh api 'repos/Jose22Yt/FlexyGram/environments/flexygram-beta/deployment-branch-policies?per_page=100'
   gh api repos/Jose22Yt/FlexyGram/branches/main
   ```

6. Registrar en `.github/beta/policy.json` el `environment_id` numérico real y todos los `reviewer_ids` numéricos devueltos. Inspeccionar la interfaz, marcar los controles `ui_review` verdaderos solo cuando se hayan comprobado, indicar `reviewed_by` y `reviewed_at` UTC (`YYYY-MM-DDTHH:MM:SSZ`). Revisar en otro PR. Un nombre de entorno o un JSON de ejemplo no demuestra protección. `confirmed:false` y los campos vacíos iniciales son intencionados.
7. Ejecutar localmente `python3 .github/beta/audit_environment.py --owner-check` (puede usar `GH_TOKEN` de la sesión local, nunca subirlo ni añadirlo a los secretos del build). Ejecutar después Actions → **Official Beta private ARM64** → Run workflow → rama `main` → `mode=audit`. No introduce claves y no entra al job de firma. Los errores API/403/404 y cualquier deriva bloquean; no se omiten los controles para continuar. El workflow usa su token efímero con `actions:read`, sin PAT administrativo. Si el API no permite inspeccionar las protecciones en esa instalación, resolver el acceso antes de cargar secretos.

La auditoría comprueba en vivo: ID y nombre del entorno, revisores exactos, autoaprobación prohibida, política custom exclusiva `Branch: main`, main protegida y procedencia del workflow. La prohibición de bypass, reglas detalladas de main, alcance de secretos y destinatario se respaldan mediante revisión manual registrada; no hay una garantía automática de esos controles si un administrador los cambia sin actualizar el registro. Revisarlos otra vez al aprobar cada build. Un administrador capaz de cambiar reglas y código sigue siendo parte de la confianza del sistema.

Observación de preparación (2026-10-30): API público de main devuelve `protected:true`; los GET públicos del entorno y sus ramas devolvieron 404. **No constituye confirmación de existencia ni de protecciones del entorno.** No se ha inspeccionado su interfaz administrativa ni se han cargado credenciales.

## Entrega cifrada: preparar antes del build

Instalar `age` en el equipo privado que recibirá la APK y crear allí una identidad **de cifrado de entrega**, independiente de la firma Android:

```bash
age-keygen -o flexygram-delivery-identity.txt
age-keygen -y flexygram-delivery-identity.txt
```

Esto NO crea otra llave de firma Android ni reemplaza el PKCS12. Guardar la identidad de entrega localmente, fuera de repositorios/chat. Copiar únicamente el destinatario público `age1...` al campo revisado `ui_review.delivery_age_recipient` y a la variable de entorno GitHub **FLEXYGRAM_BETA_AGE_RECIPIENT**. El build exige igualdad exacta; `age` valida la clave real. Su pérdida impide descifrar la entrega; conservar respaldo privado. Nunca cargar la identidad privada de entrega en GitHub.

Los artefactos del repositorio público pueden ser accesibles a otros usuarios autenticados: por ello SOLO se sube un `.tar.age` cifrado para ese destinatario, con retención de un día. El APK, los reportes internos, las credenciales y las claves no se publican en claro. La privacidad depende de verificar el destinatario correcto antes de aprobar el build.

## Siete secretos definitivos, exclusivamente del entorno

En Settings → Environments → flexygram-beta → Environment secrets, no en secrets de repositorio/organización:

| Nombre | Contenido |
| --- | --- |
| `FLEXYGRAM_RELEASE_KEYSTORE_B64` | Base64 de una sola línea del **PKCS12 oficial existente** del propietario. |
| `FLEXYGRAM_RELEASE_STORE_PASSWORD` | Contraseña exacta del almacén. |
| `FLEXYGRAM_RELEASE_KEY_PASSWORD` | Contraseña exacta de la entrada; si es igual, repetirla en este secreto. |
| `FLEXYGRAM_RELEASE_KEY_ALIAS` | `flexygram-release`. |
| `TELEGRAM_APP_ID` | ID autorizado del propietario, no identificadores heredados/de ejemplo. |
| `TELEGRAM_APP_HASH` | Hash autorizado correspondiente, 32 caracteres hexadecimales. |
| `FLEXYGRAM_BETA_FIREBASE_JSON_B64` | Base64 de una sola línea de `google-services.json` para Beta. |

Una variable pública de entorno adicional: `FLEXYGRAM_BETA_AGE_RECIPIENT`. No hacen falta tokens de Telegram, credenciales Alpha, contraseña de entrega, `LOCAL_PROPERTIES`, un pin configurable ni un PAT administrativo para compilar. Verificar en la interfaz que los siete nombres existen como **Environment secrets**; GitHub puede resolver nombres también desde el repositorio si faltan en el entorno, y el runner no prueba por sí solo su procedencia. Marcar `only_environment_scoped_beta_secrets` solo tras comprobarlo. No eliminar ni rotar credenciales existentes de otros workflows.

Codificar el archivo localmente sin imprimirlo ni pegarlo en chat. Con GitHub CLI autenticado, esta plantilla lee el archivo desde el equipo del propietario y envía su Base64 directamente a GitHub (cambiar solo la ruta; ejecutar después de la auditoría):

```bash
python3 -c 'import base64,pathlib,sys; sys.stdout.write(base64.b64encode(pathlib.Path(sys.argv[1]).read_bytes()).decode())' '/ruta/privada/oficial.p12' | gh secret set FLEXYGRAM_RELEASE_KEYSTORE_B64 --repo Jose22Yt/FlexyGram --env flexygram-beta
```

Para contraseñas y demás valores usar **Add environment secret** o el prompt privado de `gh secret set NOMBRE --repo Jose22Yt/FlexyGram --env flexygram-beta`; no pasar contraseñas por argumentos, scripts, commits o mensajes. GitHub cifra sus secretos; Base64 solo representa bytes para transportarlos. Su límite de tamaño por secreto aplica también al Base64 (48 KB); no fraccionar ni cambiar controles sin revisar el procedimiento.

## Firebase Beta

En el proyecto Firebase autorizado, registrar/seleccionar la app Android con paquete exacto `com.flexygram.messenger`. Añadir las huellas del certificado público oficial si los servicios lo requieren; no usar la huella Alpha/Debug. Descargar su `google-services.json` localmente. Confirmar `client[].client_info.android_client_info.package_name`; si existen otros clientes, debe estar presente el cliente Beta correcto. La validación de Gradle permanece obligatoria.

```bash
python3 -c 'import base64,pathlib,sys; sys.stdout.write(base64.b64encode(pathlib.Path(sys.argv[1]).read_bytes()).decode())' '/ruta/privada/google-services.json' | gh secret set FLEXYGRAM_BETA_FIREBASE_JSON_B64 --repo Jose22Yt/FlexyGram --env flexygram-beta
```

No commitear el JSON. El workflow lo reconstruye en directorio temporal exterior, permiso 0600, y crea solo un enlace temporal `source/TMessagesProj/src/beta/google-services.json`, requerido por el plugin de Google. El PKCS12 nunca entra al checkout, ni como copia ni como enlace.

## Compilación, verificación y retirada

Runner GitHub hospedado y efímero Ubuntu24.04; Java21/Python3.11; SDK37 real/build-tools36.0.0, NDK27.2.12479018 y CMake3.31.6; submódulos recursivos fijados por PR141; reconstrucción de ruedas Python ARM64 de 16 KB mediante el helper ya revisado. `ALPHA_WHEELHOUSE` es el nombre heredado del directorio de dependencias nativas compartidas, no una variante ni una identidad de firma. No se importan secretos Alpha. Solo se adapta temporalmente la selección de proveedor JDK a ADOPTIUM, sin modificar las fuentes de aplicación. No se restauran/suben caches de Gradle ni entradas privadas.

Tras la auditoría repetida y aprobación del entorno, se reconstruyen y validan entradas, y se ejecuta exactamente:

```bash
NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:assembleBeta --no-daemon --console=plain
python3 tools/beta_release/verify_beta_apk.py /ruta/al/apk --build-tools "$ANDROID_HOME/build-tools/36.0.0"
```

Se conservan todos los gates Gradle de correspondencia privada/pública, PKCS12/alias, huella fija y Firebase. El verificador intacto de PR141 comprueba el APK real: única firma oficial, esquemas v2/v3, paquete/versión/etiquetas, ARM64/96ELF, alineación16KB, manifest/identidad. El orquestador añade CRC ZIP, una única APK, código1290 exacto, hash y procedencia. Cualquier fallo bloquea la entrega; no hay fallback Debug/Alpha ni generación de firma.

La salida de comandos privados va a un log temporal, no al log público; ante fallo se informa solamente la etapa. Ningún log privado se sube. Finalmente se eliminan fuente temporal, productos APK/DEX/JNI, Firebase, PKCS12, logs y Gradle privado mediante `finally` y otro paso `if:always()`, antes de cualquier upload. La copia cifrada se elimina del runner tras subirla. En una interrupción forzada no se puede garantizar ejecución de cleanup; el runner efímero debe destruirse. No usar runners self-hosted. Los builds ejecutan Gradle/submódulos del commit revisado y acciones fijadas por SHA; las dependencias y toolchains descargadas conservan los riesgos de suministro heredados, no se afirma que esta infraestructura los elimine.

Descargar el artefacto del run verificado desde Actions, descomprimir el ZIP contenedor si corresponde y, en el equipo privado:

```bash
age --decrypt --identity flexygram-delivery-identity.txt --output FlexyGram-Beta-1290.tar FlexyGram-Beta-1290.tar.age
tar -xf FlexyGram-Beta-1290.tar
sha256sum FlexyGram-Beta-1290-ARM64.apk
```

Comparar el SHA con `verification.json` y `provenance.json`, comprobar `source_commit` PR141 y `dispatcher_commit` del run aprobado. Repetir el verificador original localmente con Android build-tools. No instalar si difiere ningún dato. Retirar el artefacto al descargarlo o esperar su vencimiento; no compartir la identidad de descifrado. Probar instalación/actualización con identidad oficial, arranque/login, funciones y desplazamiento en Poco X8 Pro. Esta aceptación física queda pendiente; no se deduce fluidez de pruebas host ni de compilar.

## Evidencia sin credenciales reales

Ejecutar `python3 -m unittest discover -s .github/beta -p 'test_*.py' -v` con PyYAML6.0.3 y `age` instalados. El workflow separado **Beta private infrastructure tests (no secrets)** corre en PR sin entorno ni secretos. Incluye recorrido de éxito con APK sintética, build/verificador simulados, cifrado/descifrado age reales, limpieza tras fallos de build/verificación/cifrado y múltiples rechazos de políticas/entradas/procedencia. No genera ninguna llave de firma: la única clave de prueba es de cifrado de entrega desechable.

Eso prueba el cableado y los controles de infraestructura. **No prueba todavía descarga/compilación completa de SDK/JNI/DEX, acceso real a secretos, aprobación real del entorno, firma oficial, instalación o rendimiento.** `mode=audit` real solo podrá pasar una vez que el propietario haya creado y revisado las protecciones. No cargar secretos basándose únicamente en pruebas con fixtures.
