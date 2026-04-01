# Metal MVP

Base para un MVP web orientado a metalurgica. Esta Fase 4 extiende la app Flask existente con carga y almacenamiento seguro de archivos STEP/IGES para piezas individuales.

## Alcance actual

- App Flask funcional con patron app factory
- Configuracion por entorno (`development`, `testing`, `production`)
- Persistencia real con SQLAlchemy y SQLite
- Dashboard y CRUD web de proyectos/piezas
- Carga de archivos `.step`, `.stp`, `.iges` e `.igs`
- Guardado seguro de archivos en `uploads/`
- Registro de metadata en `UploadedModel`
- Visualizacion y descarga del archivo asociado desde la UI
- Manejo amigable de errores y mensajes flash

## Modelos disponibles

- `Project`
- `UploadedModel`
- `DrawingJob`
- `ExportFile`
- `Template`

## Datos de gestion disponibles en Project

- nombre de pieza
- codigo de pieza
- revision
- observaciones
- material opcional
- autor opcional
- template seleccionado opcional
- estado

## Flujo de upload actual

1. Crear una pieza desde la UI.
2. Entrar al detalle del proyecto.
3. Subir un archivo valido con extension `.step`, `.stp`, `.iges` o `.igs`.
4. El archivo se guarda con nombre seguro dentro de `uploads/project_<id>/`.
5. La metadata queda registrada en SQLite en `UploadedModel`.
6. El archivo aparece listado en el detalle del proyecto con opcion de descarga.

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
```

## Testing

```bash
pytest
```

## Estado funcional de la Fase 4

- Ya podes crear proyectos y subirles archivos STEP/IGES validos.
- Los archivos quedan almacenados de forma segura en `uploads/`.
- La metadata queda persistida en SQLite.
- La vista de detalle muestra los archivos asociados y permite descargarlos.
- Todavia no hay importacion real con FreeCAD.
- Todavia no hay drawing generation, exportacion ni Ollama.

## Como retomar si se interrumpe

1. Revisar `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
2. Activar `.venv`.
3. Ejecutar `python init_db.py` para asegurar la base.
4. Validar con `pytest`.
5. Levantar la app con `python run.py`.
6. Continuar unicamente con la siguiente fase pendiente, reutilizando la estructura actual.
