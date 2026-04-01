# Changelog

## 2026-03-31

- Se implemento la Fase 6 sobre la base existente sin rehacer el proyecto.
- Se agrego `app/cad/techdraw_service.py` como capa base para generar drawing preliminar 2D.
- Se incorporo una arquitectura preparada para TechDraw con fallback SVG controlado.
- Se agrego persistencia del drawing mediante `DrawingJob` y `ExportFile`.
- Se incorporo la accion `Generar drawing` desde el detalle del proyecto.
- Se muestra en la UI el estado del drawing y un preview SVG basico cuando existe.
- Se ampliaron las pruebas para cubrir generacion y preview del drawing preliminar.
