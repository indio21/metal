# Next Steps

## Estado actual

La version 2.0 del MVP ya quedo cerrada con:

- analisis CAD base
- clasificacion axial o torneada
- deteccion de eje dominante
- estrategia de vistas especializada
- hoja axial preliminar con:
  - lateral principal
  - extremo
  - corte longitudinal
  - cajetin
  - notas generales
  - acotado basico
  - exportacion SVG, PDF y DXF
- asistencia opcional con Ollama o fallback local

## Siguiente fase exacta

Si se continua despues del cierre del MVP, el siguiente bloque razonable de mejoras seria:

- refinar la similitud visual con el ejemplo del cliente
- mejorar deteccion de escalones, radios y chaflanes reales desde la geometria
- reforzar el corte longitudinal con interior mas fiel
- preparar una etapa de revision manual asistida o reglas mas finas de taller

## Restricciones a respetar

- no rehacer el proyecto desde cero
- no borrar trabajo correcto salvo necesidad justificada
- mantener el proyecto ejecutable al final de cada fase
- no introducir todavia GD&T completo
- mantener el foco en piezas individuales axiales
- no prometer acotado universal perfecto
- mantener Ollama como opcional

## Como retomar si se interrumpe

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Activar `.venv`.
4. Ejecutar `pip install -r requirements.txt`.
5. Ejecutar `.\.venv\Scripts\python.exe init_db.py`.
6. Validar con `.\.venv\Scripts\python.exe -m pytest`.
7. Levantar la app con `.\.venv\Scripts\python.exe run.py`.
8. Continuar solo con una mejora incremental bien acotada.
