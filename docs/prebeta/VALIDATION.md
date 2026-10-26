# Validación de la rama de identidad y auditoría

Base: Alpha1274 `8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881`. Frontera Work1 revisada de nuevo en `ab7b16ff816e353d069c8bd064f5417d4dc22f92` (35 archivos respecto a la base). El snapshot es una revisión identificada, no una promesa de que la rama activa deje de cambiar.

| Control ejecutado | Resultado y alcance |
| --- | --- |
| Auditoría dedicada |10 pruebas aprobadas: documentación/enlaces, archivo histórico/licencia exactos, inventarios deterministas, guards heredados, parche aislado/reversible y política staged |
| Política Java compilada y ejecutada |109 comprobaciones aprobadas de canal, repositorio/URL, paquete, certificado/signers, versionado, tamaño e integridad; evidencia de archivo doblada explícitamente en esos casos |
| SDK real | AAPT2/API37 compila/enlaza los valores de marca preparados, con application label de probe; no es el manifest completo del cliente |
| Firma real de fixture | keytool + apksigner V2 en APK mínimo temporal; AAPT2 lee paquete/versionCode; la política real rechaza el certificado de prueba; modificación posterior invalida V2. No se usa ni genera una firma de FlexyGram |
| Regresión Connected Alpha |219 pruebas host aprobadas, fuente/JNI verificadas; codec actual5088 comprobaciones con5000 mutaciones. No equivalen a una ejecución Android completa |
| Pruebas generales |144 aprobadas,31 omitidas por corpus opcionales/informe R8 no disponibles |
| Frontera de producción | Fuentes de aplicación, manifiesto, build, submódulos fijados y distribución privada sin cambios respecto a Alpha1274; solo documentación, pruebas/inventario y archivos staged |
| Compilación/aceptación de cliente | No se compila ni distribuye una APK de FlexyGram en esta misión; manifest combinado, instalación/actualización y pruebas físicas pendientes de integración coordinada con Work1 |

Comandos reproducibles:

```sh
python3 -m unittest discover -s tools/connected_alpha/prebeta -p 'test_*.py' -v
python3 tools/connected_alpha/run_checks.py
```

El SDK36/API37 y keytool son necesarios para los dos ensayos reales; su ausencia produce omisión explícita, nunca PASS Android simulado. El workflow específico instala esas herramientas y no recibe secretos ni sube APKs/keystores de prueba. El workflow existente para ramas Connected Alpha conserva sus propias pruebas de regresión; no se modifica para habilitar builds o entregas.

La ampliación del inventario en `studio_contract.py` autoriza únicamente los archivos explícitos de esta auditoría. Las comprobaciones históricas de fuentes, P0, identidad y firma no se eliminan. El antiguo README se conserva byte a byte como documento histórico; sus instrucciones no se vuelven a presentar como procedimiento actual.

Los nombres Android señalados no cambian en producción hasta aplicar el parche separado después de1275. El actualizador propuesto está fuera de la aplicación y devuelve runtime desactivado. El inventario de licencias no sustituye SBOM de una distribución ni verificación de todos los derechos gráficos. Las condiciones de Telegram pendientes y la publicación heredada son bloqueos de preparación, no problemas ocultados por CI verde.
