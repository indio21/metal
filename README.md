# Metal MVP

Base para un MVP web orientado a metalurgica. Esta Fase 7 extiende la app Flask existente con generacion de drawing preliminar 2D, preview SVG y exportacion a PDF/DXF para piezas individuales.

## Alcance actual

- App Flask funcional con patron app factory
- Configuracion por entorno (`development`, `testing`, `production`)
- Persistencia real con SQLAlchemy y SQLite
- Dashboard y CRUD web de proyectos/piezas
- Carga segura de archivos `.step`, `.stp`, `.iges` e `.igs`
- Analisis base de modelos desde el detalle del proyecto
- Generacion de drawing preliminar 2D desde la UI
- Arquitectura base tipo TechDraw con fallback SVG controlado
- Registro del drawing en `DrawingJob` y `ExportFile`
- Preview SVG basico del plano generado
- Exportacion desacoplada a PDF y DXF desde el detalle del proyecto
- Historial de exportaciones por pieza con descarga directa

## Modelos disponibles

- `Project`
- `UploadedModel`
- `DrawingJob`
- `ExportFile`
- `Template`

## Flujo de drawing actual

1. Crear una pieza desde la UI.
2. Subir un archivo valido STEP/IGES en el detalle del proyecto.
3. Ejecutar `Analizar modelo` sobre el archivo asociado.
4. Ejecutar `Generar drawing`.
5. Revisar el preview SVG generado en el detalle del proyecto.
6. Exportar el drawing a `PDF` o `DXF`.
7. Descargar cada exportacion desde el historial del proyecto.
8. Si el entorno dispone de FreeCAD/TechDraw, la arquitectura queda preparada para usarlo.
9. Si no esta disponible, se genera una hoja SVG preliminar equivalente usando el analisis previo.
10. El resultado se guarda en `DrawingJob` y `ExportFile`, y se muestra en el detalle.

## Configuracion de FreeCAD

La app sigue funcionando aunque FreeCAD no este instalado. En ese caso:

- el upload sigue operativo
- el analisis queda en fallback controlado
- la generacion de drawing usa el generador SVG preliminar
- la exportacion PDF/DXF sigue disponible si las dependencias Python estan instaladas
- el usuario ve un error amigable en la UI

### Windows

1. Instalar FreeCAD.
2. Identificar la carpeta que contiene los modulos Python de FreeCAD. En Windows suele ser algo como:

```text
C:\Program Files\FreeCAD 0.21\bin
```

3. Configurar la variable de entorno:

```powershell
$env:FREECAD_LIB_PATH="C:\Program Files\FreeCAD 0.21\bin"
```

4. Reiniciar la terminal o VS Code si hace falta.
5. Ejecutar:

```bash
python init_db.py
python run.py
```

Si `FREECAD_LIB_PATH` no apunta a una instalacion valida, la app mostrara el fallback de error controlado.

## Dependencias de exportacion

La Fase 7 agrega estas dependencias Python:

- `reportlab` para generar PDF
- `ezdxf` para generar DXF

Quedan incluidas en `requirements.txt`. Si el entorno no las tiene instaladas, la UI muestra un mensaje claro al intentar exportar.

## Estructura del proyecto

```text
/app
  /routes
  /services
  /models
  /templates
  /static
  /utils
  /cad
  /ai
/uploads
/exports
/tests
run.py
init_db.py
config.py
requirements.txt
README.md
CHANGELOG.md
NEXT_STEPS.md
```

## Puesta en marcha

1. Activar el entorno virtual:

```bash
.venv\Scripts\Activate.ps1
```

2. Instalar dependencias si hace falta:

```bash
pip install -r requirements.txt
```

3. Inicializar o sincronizar la base de datos:

```bash
python init_db.py
```

4. Ejecutar la app:

```bash
python run.py
```

5. Abrir `http://127.0.0.1:5000`

## Variables de entorno

La app funciona sin archivo `.env`, pero se puede personalizar con:

```env
APP_ENV=development
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///metal.db
FREECAD_LIB_PATH=C:\Program Files\FreeCAD 0.21\bin
```

## Testing

```bash
pytest
```

## Estado funcional de la Fase 7

- Ya podes crear proyectos y subirles archivos STEP/IGES validos.
- Ya podes intentar analizar un modelo desde el detalle del proyecto.
- Ya podes generar un drawing preliminar 2D desde el detalle del proyecto.
- El preview basico queda persistido como SVG y asociado al proyecto.
- Ya podes exportar el drawing a PDF y DXF desde el detalle del proyecto.
- Ya podes descargar las exportaciones y consultar su historial por pieza.
- Si FreeCAD esta disponible, la arquitectura queda lista para integrarlo de forma mas profunda.
- Si FreeCAD o TechDraw no estan disponibles, la app usa un fallback SVG controlado y mantiene el flujo operativo.
- Todavia no hay Ollama.

## Como retomar si se interrumpe

1. Revisar `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
2. Activar `.venv`.
3. Ejecutar `pip install -r requirements.txt` si falta alguna dependencia de exportacion.
4. Si queres analisis/drawing con FreeCAD, verificar `FREECAD_LIB_PATH`.
5. Ejecutar `python init_db.py` para asegurar la base.
6. Validar con `pytest`.
7. Levantar la app con `python run.py`.
8. Continuar unicamente con la siguiente fase pendiente, reutilizando la estructura actual.
