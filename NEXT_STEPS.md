# Next Steps

## Estado actual

La Fase 6 quedo completa con generacion de drawing preliminar 2D y preview SVG basico asociado a piezas individuales.

## Siguiente fase exacta

Continuar con la Fase 7 enfocandose en:

- exportacion util del drawing a formatos finales o intermedios
- consolidacion de salida PDF, DXF y SVG
- mejor separacion entre preview y archivo final
- estructura para colas o jobs de exportacion
- mensajes de estado mas detallados para cada formato

## Restricciones a respetar

- No agregar Ollama en esta fase.
- Mantener compatibilidad con entornos donde FreeCAD no este instalado.
- No prometer acotado universal ni layout final perfecto aun.
- Mantener el foco en piezas individuales.

## Como retomar el trabajo

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Activar `.venv`.
4. Si queres analisis/drawing con FreeCAD, verificar `FREECAD_LIB_PATH`.
5. Ejecutar `python init_db.py`.
6. Validar con `pytest`.
7. Levantar la app con `python run.py`.
8. Continuar solo con la proxima fase pendiente sin rehacer la base existente.
