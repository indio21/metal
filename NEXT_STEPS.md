# Next Steps

## Estado actual

La Fase 4 quedo completa con carga y almacenamiento seguro de archivos STEP/IGES asociados a proyectos individuales.

## Siguiente fase exacta

Continuar con la Fase 5 enfocandose en:

- adaptador inicial para apertura del modelo con FreeCAD
- deteccion controlada del entorno FreeCAD
- lectura basica de metadata geométrica o del documento
- stubs funcionales para analisis del modelo
- mensajes de fallback claros cuando FreeCAD no este disponible

## Restricciones a respetar

- No implementar todavia drawing generation completo.
- No agregar exportacion PDF/DXF/SVG en esta fase.
- Mantener Ollama como opcional y aun sin dependencia obligatoria.
- Evitar asumir que FreeCAD estara instalado en todos los entornos.

## Como retomar el trabajo

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Activar `.venv`.
4. Ejecutar `python init_db.py`.
5. Validar con `pytest`.
6. Levantar la app con `python run.py`.
7. Continuar solo con la proxima fase pendiente sin rehacer la base existente.
