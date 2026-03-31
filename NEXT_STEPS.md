# Next Steps

## Estado actual

La Fase 2 quedo completa con persistencia real de proyectos, modelos base del dominio, listado, alta y detalle funcionando sobre SQLite.

## Siguiente fase exacta

Continuar con la Fase 3 enfocandose en:

- carga controlada de archivos `STEP`, `STP`, `IGES` e `IGS`
- validaciones de extension, nombre y tamano
- almacenamiento fisico en `uploads/`
- creacion real de registros `UploadedModel`
- asociacion del archivo CAD al proyecto
- mensajes de error claros para archivos no soportados

## Restricciones a respetar

- No implementar todavia FreeCAD ni TechDraw.
- No generar drawings 2D en esta fase.
- No agregar exportacion PDF/DXF/SVG en esta fase.
- Mantener Ollama como opcional y aun sin dependencia obligatoria.

## Como retomar el trabajo

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Activar `.venv`.
4. Ejecutar `python init_db.py`.
5. Validar arranque con `python run.py`.
6. Continuar solo con la proxima fase pendiente sin rehacer la base existente.
