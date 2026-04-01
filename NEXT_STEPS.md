# Next Steps

## Estado actual

Las Fases 4 y 5 de la version 2.0 ya quedaron cubiertas:

- analisis CAD base
- clasificacion axial o torneada
- deteccion de eje dominante
- estrategia de vistas especializada
- preview base de:
  - lateral principal
  - extremo
  - corte longitudinal

## Siguiente fase exacta

Continuar con la siguiente fase de la version 2.0 enfocandose en:

- consolidar el drawing tecnico similar al ejemplo del cliente
- mejorar layout, marco y cajetin
- empezar a ubicar cotas basicas utiles
- preparar exportacion final vectorial especializada

## Restricciones a respetar

- no rehacer el proyecto desde cero
- no borrar trabajo correcto salvo necesidad justificada
- mantener el proyecto ejecutable al final de cada fase
- no introducir todavia GD&T completo
- mantener el foco en piezas individuales axiales

## Como retomar si se interrumpe

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Activar `.venv`.
4. Ejecutar `pip install -r requirements.txt`.
5. Ejecutar `python init_db.py`.
6. Validar con `pytest`.
7. Levantar la app con `python run.py`.
8. Continuar solo con la siguiente fase pendiente de la version 2.0.
