# P0.2 — Validación Android offline obligatoria antes de beta

**BLOQUEO DE CUALQUIER BETA DISTRIBUIBLE.** Las correcciones de código independientes pueden continuar. P0.2 integrado solo como código, sin validación de ejecución. PR #5 aprobado en `7ce7ba1d8c4a35d0c15586a2ddb36cf65bf09acc`; integración develop `d31d0e780fe133337b343379563d65f579acf14d`.

**Issue todavía no creado:** GitHub devuelve 410 porque Issues está desactivado. Este es su contenido listo para publicación. Habilitar Issues no equivale a habilitar Actions.

## Requisitos de cierre

- [ ] Instalación limpia ARM64 bajo paquete independiente y primer arranque.
- [ ] Sin cierres inesperados/ANR; segundo plano y reapertura.
- [ ] Sin tráfico observado por UID, IPv4 e IPv6, indicando alcance de la captura.
- [ ] Permisos/componentes efectivos coinciden con contrato; sin diálogos sensibles.
- [ ] Autenticación imposible, sin cuentas/sesiones restauradas ni plugins/servicios heredados.
- [ ] Compatibilidad de bibliotecas con páginas de 16 KB, con tamaño de página real verificado. Cuatro bibliotecas Python (exslt, freetype, xml2 y xslt) tienen hallazgos pendientes: no certificar 16 KB con una prueba 4 KB ni con el motor sin ejercitar.
- [ ] Evidencias depuradas y revisión explícita del responsable antes de beta.

## Laboratorio reproducible (no ejecutado en Work)

Preparar Android Studio, Emulator, Platform Tools y un AVD ARM64 AOSP con `adb root`, sin Play Store/cuentas/Telegram/datos personales. Usar equipo dedicado, sin teléfonos personales conectados. Aprovisionar herramientas antes de desconectar Internet del host. El artefacto se maneja solo internamente con autorización, nunca se adjunta a este issue/PR.

Iniciar un AVD nuevo (wipe-data borra únicamente ese AVD desechable):

```bash
emulator @FlexyGramLab -wipe-data -no-snapshot
export ANDROID_SERIAL=emulator-5554
export PKG=io.github.jose22yt.flexygram.diagnostic
mkdir -p evidencia-p02
adb get-state
adb shell getprop ro.kernel.qemu
adb shell getprop ro.product.cpu.abilist
adb shell getconf PAGE_SIZE
adb root
adb wait-for-device
adb shell id
```

Exigir emulador esperado, qemu=1, arm64-v8a y root. Registrar Android/huella de imagen/versiones de herramientas/página. Si no se cumplen, detenerse sin sustituirlo por un dispositivo personal. Primera ejecución 4 KB; una ejecución 16 KB debe registrarse aparte.

Verificar hash, procedencia y firma del artefacto autorizado, sin recompilar aquí. Hash histórico del APK interno final de P0.2: `c2769a9a5405574f6b8bb3995262db4a03ce058b8e8d471864237aaaaa01e211`; certificado SHA256 `40e31874e6d50f8166f565c721ee312021c065eccf79e0f8d4d3c4cfec87d3e6`. Un binario posterior tendrá su propia correspondencia commit/hash; no asumir igualdad.

```bash
export APK=/ruta/local/al/artefacto-autorizado.apk
shasum -a 256 "$APK"
adb shell pm path "$PKG"
# Solo si el paquete no estaba instalado y el artefacto está verificado:
adb install --no-streaming "$APK"
adb shell dumpsys package "$PKG" > evidencia-p02/paquete.txt
adb shell svc wifi disable
adb shell svc data disable
adb shell cmd package list packages -U "$PKG"
```

Copiar el UID numérico exacto a APP_UID. **Antes del primer arranque**, instalar reglas nuevas exclusivas de ese UID en ambas familias. Cualquier fallo requiere detenerse, sin vaciar reglas globales:

```bash
export APP_UID=NUMERO_OBTENIDO
for herramienta in iptables ip6tables; do
  adb shell "$herramienta -w -N FLEXYGRAM_P02" || exit 1
  adb shell "$herramienta -w -A FLEXYGRAM_P02 -j DROP" || exit 1
  adb shell "$herramienta -w -I OUTPUT 1 -m owner --uid-owner $APP_UID -j FLEXYGRAM_P02" || exit 1
done
for herramienta in iptables ip6tables; do
  adb shell "$herramienta -w -S OUTPUT"
  adb shell "$herramienta -w -nvxL FLEXYGRAM_P02"
done > evidencia-p02/red-antes.txt
adb logcat -c
adb shell am start -W -n "$PKG/org.telegram.messenger.ExteralessIcon" \
  -a android.intent.action.MAIN -c android.intent.category.LAUNCHER \
  > evidencia-p02/arranque.txt
```

Observar >=60 s, pasar a segundo plano/reabrir una vez. No introducir teléfonos reales, OTP, QR, claves ni sesiones. Solo valores ficticios si una comprobación exige entrada, manteniendo bloqueo de red. Confirmar ausencia de permisos peligrosos, INTERNET, servicios de cuenta/push/media/car/wear, carga de plugins/Python o restauración de sesiones. El launcher permitido debe seguir disponible y JLatexMathInitProvider privado puede inicializar recursos locales.

Probar rechazo externo de componentes deshabilitados:

```bash
adb shell am startservice -n "$PKG/org.telegram.messenger.WearAuthListenerService"
adb shell am startservice -n "$PKG/org.telegram.messenger.car.TelegramCarAppService"
```

Guardar respuestas de rechazo y evidencias finales:

```bash
adb shell pidof "$PKG" > evidencia-p02/proceso.txt
adb shell dumpsys activity activities > evidencia-p02/actividades.txt
adb shell dumpsys activity services "$PKG" > evidencia-p02/servicios.txt
adb logcat -b crash -d > evidencia-p02/crash.txt
adb logcat -d -v threadtime > evidencia-p02/logcat.txt
for herramienta in iptables ip6tables; do
  adb shell "$herramienta -w -S OUTPUT"
  adb shell "$herramienta -w -nvxL FLEXYGRAM_P02"
done > evidencia-p02/red-despues.txt
adb shell am force-stop "$PKG"
```

## Aceptación y límites

Cada requisito se marca APROBADO/FALLIDO/NO VERIFICADO y se acompaña de salidas, fecha, imagen, herramientas, commit/binario/hash, UID y página. Exigir proceso estable, ningún permiso sensible solicitado, rechazo de componentes prohibidos, sin sesiones, sin incremento de paquetes IPv4/IPv6. Un contador positivo detecta paquetes bloqueados y obliga a investigar; no afirmar ausencia de intentos porque no llegaron al exterior.

Contadores cero solo prueban ausencia de paquetes en ese punto para ese UID: no todas las llamadas API ni tráfico delegado a otros UID. Host desconectado impide egress delegado. Una instalación nueva no acredita todos los escenarios de restauración/migración. Añadir pruebas de restauración con fixtures sintéticos en laboratorio y documentar variante/OEM. La compatibilidad integral 16 KB requiere ELF, empaquetado y carga real de las bibliotecas pertinentes, sin habilitar Python/plugins/auth ni cambiar guardas sin autorización adicional.

Revisar logs antes de compartir. No adjuntar APK, claves, bases, preferencias privadas, conversaciones, dumps de cuenta ni bugreports personales. Destruir únicamente el AVD desechable al terminar. Cualquier fallo/no verificado mantiene el bloqueo de beta. No cerrar este pendiente por pruebas unitarias o BUILD SUCCESSFUL.
