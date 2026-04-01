# Next Steps

## Estado actual

El MVP base quedo navegable y retomable:

- gestion de proyectos/piezas
- carga STEP/IGES
- analisis CAD base con fallback controlado
- analisis CAD con identificacion visible entre FreeCAD real y modo demo de la app
- drawing preliminar 2D
- preview SVG
- exportacion PDF/DXF
- asistencia opcional con Ollama o ayuda local

## Como continuar sin perder contexto

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Activar `.venv`.
4. Ejecutar `pip install -r requirements.txt`.
5. Ejecutar `python init_db.py`.
6. Validar con `pytest`.
7. Levantar la app con `python run.py`.
8. Recién después avanzar con una mejora puntual, sin rehacer la base.

## Mejoras sugeridas despues del MVP

- integrar FreeCAD/TechDraw real con mayor profundidad cuando el entorno lo permita
- mejorar templates de plano y cajetin editable
- agregar cotas principales mas robustas
- separar preview web, archivo intermedio y salida final
- agregar cola simple de jobs para analisis y exportacion
- versionar mejor los drawings por revision
- mejorar permisos, auditoria y trazabilidad si el uso crece
- ampliar la asistencia IA con prompts mas contextualizados sin volverla obligatoria

## Limites a respetar en futuras iteraciones

- mantener foco en piezas individuales hasta decidir una fase dedicada a ensamblajes
- no prometer acotado universal
- no volver obligatorias ni FreeCAD ni Ollama
- no introducir dependencias pagas obligatorias
- mantener el proyecto ejecutable al final de cada fase
