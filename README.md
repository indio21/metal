# Metal MVP

Base para un MVP web orientado a metalurgica. Esta Fase 6 extiende la app Flask existente con generacion de drawing preliminar 2D para piezas individuales, usando arquitectura equivalente a TechDraw con fallback SVG controlado.

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
5. Si el entorno dispone de FreeCAD/TechDraw, la arquitectura queda preparada para usarlo.
6. Si no esta disponible, se genera una hoja SVG preliminar equivalente usando el analisis previo.
7. El resultado se guarda en `DrawingJob` y `ExportFile`, y se muestra en el detalle.

## Configuracion de FreeCAD

La app sigue funcionando aunque FreeCAD no este instalado. En ese caso:

- el upload sigue operativo
- el analisis queda en fallback controlado
- la generacion de drawing usa el generador SVG preliminar
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

## Estado funcional de la Fase 6

- Ya podes crear proyectos y subirles archivos STEP/IGES validos.
- Ya podes intentar analizar un modelo desde el detalle del proyecto.
- Ya podes generar un drawing preliminar 2D desde el detalle del proyecto.
- El preview basico queda persistido como SVG y asociado al proyecto.
- Si FreeCAD esta disponible, la arquitectura queda lista para integrarlo de forma mas profunda.
- Si FreeCAD o TechDraw no estan disponibles, la app usa un fallback SVG controlado y mantiene el flujo operativo.
- Todavia no hay exportacion final completa ni Ollama.

## Como retomar si se interrumpe

1. Revisar `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
2. Activar `.venv`.
3. Si queres analisis/drawing con FreeCAD, verificar `FREECAD_LIB_PATH`.
4. Ejecutar `python init_db.py` para asegurar la base.
5. Validar con `pytest`.
6. Levantar la app con `python run.py`.
7. Continuar unicamente con la siguiente fase pendiente, reutilizando la estructura actual.
