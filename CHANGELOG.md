# Changelog

## 2026-03-31

- Se implemento la Fase 5 sobre la base existente sin rehacer el proyecto.
- Se agrego `app/cad/cad_import_service.py` como capa base de integracion con FreeCAD.
- Se incorporo un adaptador desacoplado con fallback controlado cuando FreeCAD no esta disponible.
- Se extendio `DrawingJob` para registrar analisis de modelo, backend y resultado serializado.
- Se agrego la accion `Analizar modelo` desde el detalle del proyecto.
- Se muestra en la UI el resultado basico del analisis o el error controlado.
- Se documento la configuracion de `FREECAD_LIB_PATH` para habilitar el analisis real.
- Se ampliaron las pruebas para cubrir analisis exitoso y fallback por falta de FreeCAD.
