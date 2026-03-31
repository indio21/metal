# Changelog

## 2026-03-31

- Se implemento la Fase 2 sobre la base existente sin rehacer el proyecto.
- Se agregaron los modelos `Project`, `UploadedModel`, `DrawingJob`, `ExportFile` y `Template`.
- Se incorporaron relaciones simples entre proyecto, drawing jobs, exports y templates.
- Se agrego sincronizacion basica del esquema para una base heredada de Fase 1.
- Se sumo seed inicial de template industrial basico.
- Se implementaron alta real, listado y detalle de proyectos con guardado en SQLite.
- Se agrego `init_db.py` como script simple de inicializacion.
- Se ampliaron las pruebas automaticas para cubrir persistencia y vistas de proyectos.
