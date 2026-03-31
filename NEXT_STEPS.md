# Next Steps

## Estado actual

La Fase 1 quedo completa con base Flask funcional, SQLite, layout Bootstrap, dashboard y placeholder de creacion de proyecto.

## Siguiente fase exacta

Continuar con la Fase 2 enfocandose en:

- alta real de proyectos
- formulario persistido en SQLite
- carga controlada de archivos `STEP`, `STP`, `IGES` e `IGS`
- validaciones basicas de nombre, extension y almacenamiento en `uploads/`
- asociacion del archivo CAD al proyecto

## Restricciones a respetar

- No implementar todavia generacion de drawings 2D.
- No integrar todavia FreeCAD ni TechDraw si no es estrictamente necesario.
- No agregar exportacion PDF/DXF/SVG en esta fase.
- Mantener Ollama como opcional y todavia sin dependencia obligatoria.

## Como retomar el trabajo

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Ejecutar `pip install -r requirements.txt` si faltan dependencias.
4. Validar arranque con `python run.py`.
5. Continuar solo con la proxima fase pendiente sin rehacer la base existente.
