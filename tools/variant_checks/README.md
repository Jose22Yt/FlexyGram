# Validación de variantes

`check_variant_graphs.py` comprueba que las tareas Alpha y Beta utilizan sus propias
validaciones de identidad y firma. Recibe dos registros reales de Gradle `--dry-run`:

```sh
python3 tools/variant_checks/check_variant_graphs.py alpha-dry-run.txt beta-dry-run.txt
```

El programa solo lee esos archivos; no compila, firma ni accede a claves.
`review.json` es el manifiesto histórico utilizado por los contratos de integración
para reproducir su revisión de referencia. Los hashes y rutas de ese registro se conservan.
