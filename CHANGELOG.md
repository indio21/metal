# Changelog

## 2026-04-01

- Se implementaron de forma incremental las Fases 6 y 7 de la version 2.0 sobre el repositorio existente.
- Se agrego `app/drawing/dimensioning_service.py` para construir acotado basico especializado en piezas torneadas:
  - longitudes axiales
  - diametros
  - radio simple
  - chaflan simple
  - notas generales
- Se agrego `app/drawing/template_service.py` para generar una hoja axial preliminar con:
  - marco exterior
  - cajetin tecnico
  - preview SVG vectorial
  - lateral principal
  - extremo
  - corte longitudinal
- Se incorporo la nueva accion `Generar hoja axial` en el detalle del proyecto.
- Se extendio `app/services/export_service.py` para exportar la hoja axial a PDF vectorial y DXF editable sin rasterizar.
- Se agrego historial de exportaciones y preview SVG dentro de la UI del proyecto.
- Se ampliaron las pruebas para cubrir generacion de hoja axial y exportaciones PDF/DXF del flujo 2.0.
- Se implementaron de forma incremental las Fases 4 y 5 de la version 2.0 sobre el repositorio existente.
- Se extendio `app/cad/cad_import_service.py` para agregar:
  - eje dominante
  - ratio axial
  - similitud transversal
  - clasificacion axial o no concluyente
  - nota de clasificacion
- Se mantuvo el adaptador de FreeCAD y el fallback controlado cuando el entorno no dispone de CAD real.
- Se agrego `app/drawing/drawing_strategy_service.py` para construir la estrategia de vistas especializada.
- Se implemento una estrategia especifica de pieza torneada con:
  - vista lateral principal
  - vista de extremo
  - corte longitudinal
- Se incorporo preview SVG base de la estrategia dentro de la UI, sin exportacion axial final todavia.
- Se actualizaron rutas y detalle del proyecto para las acciones `Analizar pieza` y `Generar estrategia de vistas`.
- Se ampliaron las pruebas para cubrir clasificacion axial y construccion de la estrategia de vistas.
