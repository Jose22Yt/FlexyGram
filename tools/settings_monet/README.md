# Iconos de ajustes

`sources/approved-icons.zip` conserva los originales aprobados de los 85 iconos Duotono
Monet. Es una entrada de importación y verificación; no es una salida de compilación.

`import_approved.py` extrae los PNG originales sin redibujarlos ni remuestrearlos y genera
los mapas de cobertura utilizados para aplicar el color del cuerpo y el acento del tema.
Requiere Python, Pillow y NumPy. La importación modifica los recursos Android: ejecútala
solo cuando se esté actualizando deliberadamente ese conjunto de recursos.

```sh
python3 tools/settings_monet/import_approved.py
python3 -m pytest tests/test_monet_assets.py -q
```

Los contratos comprueban los bytes originales, las coberturas y el catálogo. La
personalización se describe en [MONET_COMPACT_SETTINGS.md](../../docs/settings3/MONET_COMPACT_SETTINGS.md).
