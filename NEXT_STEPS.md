# Next Steps

## Estado actual

La Fase 5 quedo completa con una integracion base de analisis CAD preparada para FreeCAD y con fallback controlado cuando el entorno no lo tiene disponible.

## Siguiente fase exacta

Continuar con la Fase 6 enfocandose en:

- preparacion de la capa base para generar un drawing preliminar 2D
- stubs claros para TechDraw
- definicion de vistas frontal, superior, lateral e isometrica
- eleccion del template industrial inicial aplicado al drawing
- persistencia del job preliminar de drawing

## Restricciones a respetar

- No implementar todavia exportacion PDF/DXF/SVG final.
- No agregar Ollama en esta fase.
- Mantener compatibilidad con entornos donde FreeCAD no este instalado.
- No prometer acotado universal ni layout final completo aun.

## Como retomar el trabajo

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Activar `.venv`.
4. Si queres analisis real, verificar `FREECAD_LIB_PATH`.
5. Ejecutar `python init_db.py`.
6. Validar con `pytest`.
7. Levantar la app con `python run.py`.
8. Continuar solo con la proxima fase pendiente sin rehacer la base existente.
