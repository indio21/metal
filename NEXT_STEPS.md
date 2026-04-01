# Next Steps

## Estado actual

Las Fases 2 y 3 de la version 2.0 ya quedaron cubiertas sobre el proyecto existente:

- persistencia real para proyecto y pieza
- formulario de alta y edicion ampliado
- listado y detalle simple de proyecto
- carga segura de STEP/IGES
- registro del modelo en base de datos
- preferencia visible por STEP frente a IGES

## Siguiente fase exacta

Continuar con la fase siguiente de la version 2.0 enfocandose en:

- clasificacion basica de pieza axial o torneada
- deteccion de si el modelo pertenece a familia de revolucion
- preparacion de la estrategia de drawing especializada
- definicion de las tres vistas objetivo:
  - lateral principal
  - vista de extremo
  - corte longitudinal

## Restricciones a respetar

- no rehacer el proyecto desde cero
- no borrar trabajo correcto salvo necesidad justificada
- mantener el proyecto ejecutable al final de cada fase
- no prometer todavia el drawing final del cliente
- seguir priorizando piezas individuales

## Como retomar si se interrumpe

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Activar `.venv`.
4. Ejecutar `pip install -r requirements.txt`.
5. Ejecutar `python init_db.py`.
6. Validar con `pytest`.
7. Levantar la app con `python run.py`.
8. Continuar solo con la siguiente fase pendiente de la version 2.0.
