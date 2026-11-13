# Telegram iPhone bubble geometry

Original upstream Swift remains unmodified under `upstream/`; `provenance.json` records the immutable repository commit, source path, hash, default radii and cap coordinates. Android implementation: `IosBubbleShape.java`. Source and graphics are retained with attribution to TelegramMessenger/Telegram-iOS.

The native unit runner builds a JVM test harness, never an APK:

```bash
python tools/ios_bubbles/run_native.py --android-jar /path/to/android.jar --maven mvn --output /tmp/flexy-style-tests
```

Requires JDK21, Maven, network for test dependencies and Android SDK35. It reuses explicit isolated Telegram hosts from the existing graphics harness; Android paths, Skia rendering, layouts and accessibility are real Robolectric APIs. The service wallpaper provider is a fallback double, so this does not validate real wallpaper blur or the entire Telegram activity. Preview tick drawables are Android fixture resources, not a fidelity check of the status icons. No login/account/network-message behavior is mocked as device acceptance.

## Indicadores de envío y lectura

`status-provenance.json` fija la revisión y los hashes del código oficial. Los
vectores de conversación conservan el lienzo de 11×9 puntos, el trazo de 0,99 y
el desplazamiento de 6 puntos del original. La lista usa su geometría propia y
el grosor `1 + UIScreenPixel`, adaptado a la densidad de Android. El estado y las
transiciones siguen bajo control de Telegram Android.

El runner también comprueba las máscaras de los trazos originales, tinte y alfa
a distintas densidades, las cápsulas con RTL y fuentes ampliadas, y la reserva
de espacio de la vista previa. La prueba de máscara dibuja el `pathData` con
Android Path/Skia; no equivale a compilar recursos ni a comparar una captura de
un iPhone. El host de cabecera del escenario de distribución solo proporciona
el contrato de vista, sin validar su apariencia.
