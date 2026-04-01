# Changelog

## 2026-03-31

- Se implemento la Fase 8 sobre la base existente sin rehacer el proyecto.
- Se corrigio `app/routes/main.py`, que habia quedado corrupto, y se dejo nuevamente operativo el dashboard.
- Se agrego `app/ai/ollama_service.py` como integracion opcional y desacoplada con Ollama.
- Se incorporaron variables de entorno `OLLAMA_ENABLED`, `OLLAMA_BASE_URL` y `OLLAMA_MODEL`.
- Se agrego asistencia opcional desde el detalle del proyecto para nombre tecnico, descripcion, faltantes, cajetin y explicacion del resultado.
- Se mantuvo fallback local cuando Ollama no esta disponible o esta desactivado.
- Se actualizaron dashboard, detalle del proyecto y documentacion final del MVP.
- Se ampliaron las pruebas para cubrir fallback de Ollama y respuesta mockeada de IA.
- Se actualizo el flujo CAD para que, si FreeCAD no esta disponible, el analisis pase a un modo demo en lugar de fallar.
- Se habilito generacion de drawing y exportacion PDF/DXF aun sin FreeCAD instalado.
- Se agrego una indicacion visible en la UI para distinguir si el analisis fue hecho con FreeCAD o con el fallback interno de la app.
