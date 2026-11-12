# Pruebas de FlexyGram

La suite cubre políticas de renderizado, interacción, ajustes, recursos, ciclo de vida,
cuentas y compatibilidad con el motor de plugins. Combina comprobaciones Python con
pruebas que compilan y ejecutan clases o métodos Java de producción con dobles de sus dependencias.

## Ejecutar

Desde la raíz del repositorio, utiliza Python con `pytest` y las dependencias de las
pruebas que vayas a ejecutar. Las pruebas JVM requieren un JDK; las comprobaciones de
imágenes requieren Pillow y NumPy.

```sh
python3 -m pytest tests/ -q
python3 -m pytest tests/test_scroll_work_budget.py tests/test_render_work_reuse.py -q
```

Las utilidades Android y sus dependencias están documentadas en [tools](../tools/README.md).
Una prueba aislada no genera una APK ni acredita por sí sola el funcionamiento integrado en Android.

## Entradas opcionales

Las comprobaciones del catálogo de plugins pueden utilizar un corpus externo. Configura
`EXTERALESS_PLUGIN_CORPUS` con los archivos `.plugin` y `EXTERALESS_PLUGIN_ARCHIVES`
con los archivos `.eaf`. El corpus no forma parte del repositorio. Si falta una entrada
opcional, la prueba correspondiente se omite con su motivo.

Las pruebas R8 utilizan los resultados de `TMessagesProj/build/outputs/mapping/release/`.
Los resultados ausentes o anteriores a las reglas vigentes no se presentan como una validación actual.

## Datos de referencia

`tests/baselines/` registra límites de compatibilidad conocidos. Al resolver uno, actualiza
su referencia y conserva la comprobación que impide regresiones. No utilices datos de
cuentas reales, sesiones ni conversaciones privadas como fixtures.

Los resultados de estas pruebas deben distinguirse de una compilación completa y de
mediciones de rendimiento en dispositivo.
