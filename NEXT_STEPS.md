# Next Steps

## Estado actual

La Fase 7 queda enfocada en drawing preliminar 2D con preview SVG y exportacion PDF/DXF asociada a piezas individuales.

## Siguiente fase exacta

Continuar con la Fase 7 enfocandose en:

Continuar con la Fase 8 enfocandose en:

- consolidar templates de plano y cajetin editable mas completo
- mejorar el uso de FreeCAD/TechDraw real cuando el entorno lo permita
- enriquecer las vistas y cotas base sin prometer acotado universal
- separar con mas claridad preview web vs salida final de fabricacion
- preparar la integracion opcional con Ollama mas adelante, sin volverla obligatoria

## Restricciones a respetar

- No agregar Ollama en esta fase.
- Mantener compatibilidad con entornos donde FreeCAD no este instalado.
- No prometer acotado universal ni layout final perfecto aun.
- Mantener el foco en piezas individuales.
- Mantener la app ejecutable aun si una exportacion falla por dependencias o entorno.

## Como retomar el trabajo

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y este archivo.
3. Activar `.venv`.
4. Ejecutar `pip install -r requirements.txt` para asegurar `reportlab` y `ezdxf`.
5. Si queres analisis/drawing con FreeCAD, verificar `FREECAD_LIB_PATH`.
6. Ejecutar `python init_db.py`.
7. Validar con `pytest`.
8. Levantar la app con `python run.py`.
9. Continuar solo con la proxima fase pendiente sin rehacer la base existente.
