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
