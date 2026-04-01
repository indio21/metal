# Metal MVP 2.0

MVP web orientado a piezas torneadas, axiales o de revolucion. Esta iteracion trabaja de forma incremental sobre el repositorio existente y, en este punto, deja resueltas las Fases 2 y 3 de la version 2.0: persistencia para proyectos/piezas y gestion segura de archivos STEP/IGES.

## Estado actual

El proyecto ya permite:

1. Crear proyectos reales.
2. Registrar datos base de una pieza axial.
3. Guardar la informacion en SQLite.
4. Listar proyectos.
5. Ver un detalle simple de proyecto/pieza.
6. Subir archivos `.step`, `.stp`, `.iges` o `.igs`.
7. Guardar el archivo de forma segura en `/uploads`.
8. Persistir la metadata del modelo en base de datos.
9. Mostrar el archivo asociado en la UI.

Aunque el repo conserva capacidades heredadas de la version anterior, en esta etapa la interfaz se reenfoco en:

- persistencia
- ficha administrativa
- gestion del modelo 3D

## Reinterpretacion incremental del repositorio existente

El repositorio ya venia mas avanzado que estas fases. Para no romper continuidad:

- no se rehizo el proyecto desde cero
- no se borraron capacidades correctas
- se reinterpretaron modelos y pantallas hacia el flujo axial 2.0
- se mantuvo la app ejecutable en todo momento

## Modelos relevantes en esta etapa

- `Project`
- `UploadedModel`
- `DrawingJob`
- `ExportFile`
- `TemplateProfile`

### Campos principales incorporados o reinterpretados

`Project`
- `project_name`
- `part_name`
- `description`
- `material`
- `finish`
- `author`
- `revision`
- `notes`

`UploadedModel`
- `project_id`
- `original_filename`
- `stored_filename`
- `file_type`
- `uploaded_at`

## Regla de negocio actual

- STEP es el formato principal preferido.
- IGES se acepta como alternativa.
- La UI lo indica explicitamente al mostrar el archivo cargado.

## Stack

- Python 3.11
- Flask
- Bootstrap 5
- SQLAlchemy
- SQLite
- python-dotenv
- pytest

## Estructura actual

```text
/app
  /routes
  /services
  /models
  /templates
  /static
  /utils
  /cad
  /drawing
  /exports
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

### 1. Activar entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3. Inicializar o sincronizar la base

```powershell
python init_db.py
```

### 4. Ejecutar la app

```powershell
python run.py
```

Abrir `http://127.0.0.1:5000`.

## Variables de entorno

La base sigue soportando las variables del proyecto existente:

```env
APP_ENV=development
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///metal.db
FREECAD_LIB_PATH=C:\Program Files\FreeCAD 0.21\bin
OLLAMA_ENABLED=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

En estas fases no hace falta configurar FreeCAD ni Ollama para usar el flujo principal de persistencia + uploads.

## Testing

Ejecutar:

```powershell
pytest
```

## Limitaciones reales en este punto

- todavia no se hace clasificacion axial real
- todavia no se genera el drawing especializado de tres vistas
- todavia no se agrego la estrategia especifica de corte longitudinal
- la especializacion del plano queda para la siguiente fase

## Como retomar si se interrumpe

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
3. Activar `.venv`.
4. Ejecutar `pip install -r requirements.txt`.
5. Ejecutar `python init_db.py`.
6. Validar con `pytest`.
7. Levantar la app con `python run.py`.
8. Continuar solo con la siguiente fase pendiente de la version 2.0.
