# Changelog

## 2026-03-31

- Se implemento la Fase 4 sobre la base existente sin rehacer el proyecto.
- Se agrego una capa desacoplada de file handling en `app/services/upload_service.py`.
- Se incorporo validacion estricta para `.step`, `.stp`, `.iges` e `.igs`.
- Se implemento la subida segura de archivos desde el detalle del proyecto.
- Se guardan archivos en `uploads/` con nombre seguro y ruta por proyecto.
- Se registra metadata real en `UploadedModel` y se asocia al proyecto correspondiente.
- Se agrego listado y descarga de archivos asociados desde la UI.
- Se ampliaron las pruebas para cubrir upload valido, rechazo de formatos invalidos y descarga.
