# Relevo temporal de compilación — parches pendientes de ejecutar

Base PR23:78151d9e8083290dca2617279cab3afb53540de6.
Work1 no tiene entorno de ejecución en esta sesión: el intento inicial devolvió
"No usable execution environment is available". No hay acceso al workspace,
proceso Gradle, proxy ni caché de la sesión Work2. Ninguna compilación ejecutada aquí.

Se acepta el estado posterior comunicado por el responsable: Dropbox subió/recuperó
su prueba, Foojay se resolvió y comenzaron descargas. No se repite403 ni se declara
roto Foojay a partir del informe GitHub anterior a esos avances no publicados.

## Dos commits integrables

1. BETA-BACK-36: puente beta API33+ separado, tipos nuevos en clase anidada;
   callback delega a la misma requestClose/cola, o finish si no se creó cliente.
   Registro/cierre idempotentes; callbacks tardíos se invalidan. API24–32 mantiene
   exactamente el cuerpo legacy de onBackPressed. Doubles del host ampliados, sin
   alterar AndroidManifest/Gradle/SDK ni ApplicationLoader.
2. BETA-POSTINIT-REENTRY: latch sólo beta, a nivel de proceso, con NEW/RUNNING/READY/FAILED.
   Fallo RuntimeException/LinkageError permanece bloqueado al recrear Activity.
   READY no vuelve a ejecutar inicialización; reentrada RUNNING devuelve false.
   Otros Errors propagan y dejan estado terminal. Sin reset público, Bundle,
   credenciales, logs/excepciones retenidas ni reseteo del flag global heredado.

Se conservan BetaNavigation, LatestNavigation, eventos, animaciones, curvas/duración,
JNI, manifiestos, servicios, dependencias y contratos históricos sin editar.

## Verificación obligatoria en la sesión que tenga ejecución

**0 pruebas ejecutadas por esta sesión,0 compilaciones Java/SDK y0 APK generadas.**
Ocho métodos nuevos preparados:3 platform_back y5 postinit_reentry. Sus controles
original/corregido todavía NO acreditan reproducción ni éxito hasta ejecutarse.
Los doubles no acreditan ART/API24 ni el dispatcher real de Android16/17.

Con JDK21 disponible:
```sh
python3.11 -B -m unittest discover -s tests/beta_development -p test_platform_back.py -v
python3.11 -B -m unittest discover -s tests/beta_development -p test_postinit_reentry.py -v
```
Después ejecutar la suite beta completa normal/-O por el cambio de Activity/doubles,
con las variables de Groovy/CMake/PR24 que ya utiliza Work2. No sumar repeticiones
ni adjudicarse las60 pruebas históricas. No compilar APK antes de pasar regresiones.

## Continuar la compilación sin reiniciar trabajo innecesario

- Un solo responsable de build. Verificar si existe workspace/proceso/caché de Work2
  en el host disponible; no afirmar que se continúa un proceso de otra sesión sin verlo.
- Revisar HEAD de PR23 antes de cherry-pick; no reset/force-push sobre su rama.
  Resolver cualquier cambio concurrente antes de integrar los dos commits propios.
- Reutilizar proxy, JDK/Gradle/SDK/NDK/CMake, wheels/overlay y submódulos fijados
  que realmente estén disponibles. No sustituir versiones, certificados o TLS.
- Si la caché es inaccesible, recuperar sólo insumos imprescindibles; no atribuirle
  descargas nuevas al trabajo anterior. No repetir la búsqueda de la APK antigua.
- Crear checkout/outputs NUEVOS con la receta unsigned experimental ya existente;
  aplicar estos commits al código que se compilará, no a un checkout histórico.
- Comando objetivo, con la configuración privada recuperada:
  NATIVE_TARGET=arm64-v8a ./gradlew -PflexygramBetaDevelopment=true :TMessagesProj:assembleBetaDevelopmentDebug
  Sin SKIP; JNI y Chaquopy completos. La receta unsigned previa es necesaria:
  este comando por sí solo NO promete ausencia de firma.
- Registrar ejecución real: configuración, Java/Kotlin, JNI, Chaquopy, empaquetado y
  resultado Gradle. Un dry-run o javac con doubles no es ese build.
- Gate PR25 sobre APK real/hash nuevo y clases del mismo build. Conservar JNI/logs/
  manifest/DEX/ELF y recibos; no repinar hashes históricos.
- Antes de almacenar APK, aprobar miembros/invitaciones de /FlexyGram-Work2-Private;
  la ausencia de enlaces no enumera todos los miembros. No subir otro ZIP sintético.
- Guardar respaldo privado con nombre nuevo, descargar independientemente, comparar
  SHA256/CRC y APK/clases/commit. Mantener originales hasta recuperación comprobada.

La nueva APK no está lista para pedir firma desde esta sesión: no se generó ni verificó.
Siguen separadas las autorizaciones de clave/custodia, firma por hash, entrega,
instalación y prueba offline. No servicios remotos, Production, Actions ni Paso4.
