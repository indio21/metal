# Changelog

## 2026-04-01

- Se implementaron de forma incremental las Fases 2 y 3 de la version 2.0 sobre el repositorio existente.
- Se extendio `Project` con `project_name`, `part_name`, `description` y `finish`.
- Se reinterpretaron los nombres heredados del modelo para mantener compatibilidad con la base previa.
- Se agregaron alias utiles en `UploadedModel` para `file_type` y `uploaded_at`.
- Se incorporo `TemplateProfile` como alias semantico para la nueva version 2.0 sin romper la base existente.
- Se actualizo la sincronizacion de SQLite para agregar las nuevas columnas necesarias.
- Se adapto el formulario de alta/edicion para proyecto y pieza axial.
- Se mejoraron listado y detalle para mostrar proyecto, pieza, descripcion y terminacion.
- Se mantuvo la carga segura de STEP/IGES desde el detalle del proyecto.
- Se reforzo la regla de negocio para preferir STEP y aceptar IGES como alternativa.
- Se actualizaron las pruebas para cubrir la reinterpretacion 2.0 y la gestion del modelo.
- Se actualizaron `README.md` y `NEXT_STEPS.md` para dejar continuidad clara hacia la siguiente fase.
