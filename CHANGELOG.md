# Changelog

## 2026-03-31

- Se implemento la Fase 7 sobre la base existente sin rehacer el proyecto.
- Se agrego `app/services/export_service.py` como capa desacoplada para exportacion de drawings.
- Se incorporo exportacion a PDF mediante `reportlab`.
- Se incorporo exportacion a DXF mediante `ezdxf`.
- Se agregaron botones de exportacion y descarga desde el detalle del proyecto.
- Se muestra un historial de exportaciones por pieza en la UI.
- Se ampliaron las pruebas para cubrir exportacion y descarga de PDF/DXF.
