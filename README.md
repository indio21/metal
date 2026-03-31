# Metal MVP

Base inicial para un MVP web orientado a metalurgica. Esta Fase 2 extiende la app Flask existente con persistencia real de proyectos, relaciones base del dominio y vistas operativas para alta, listado y detalle.

## Alcance actual

- App Flask funcional con patron app factory
- Configuracion por entorno (`development`, `testing`, `production`)
- Persistencia real con SQLAlchemy y SQLite
- Dashboard inicial con acceso al flujo de proyectos
- Alta real de proyectos
- Listado de proyectos guardados
- Detalle simple de proyecto
- Modelos base del MVP preparados para fases futuras

## Modelos disponibles

- `Project`
- `UploadedModel`
- `DrawingJob`
- `ExportFile`
- `Template`

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

## Requisitos

- Python 3.11
- Entorno virtual local

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

## Estado de la base

- La aplicacion crea las tablas faltantes automaticamente al iniciar.
- Si existe una base previa de Fase 1, `init_db.py` sincroniza el esquema minimo necesario para seguir trabajando.
- Se deja seed inicial de template industrial basico para futuras fases de drawing.

## Estado funcional de la Fase 2

- Ya podes crear proyectos reales y guardarlos en SQLite.
- Ya podes listar proyectos y entrar a su detalle.
- Todavia no hay carga real de archivos STEP/IGES.
- Todavia no hay integracion con FreeCAD, drawing generation, exportacion ni Ollama.

## Como retomar si se interrumpe

1. Revisar `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
2. Activar `.venv`.
3. Ejecutar `python init_db.py` para asegurar la base.
4. Validar arranque con `python run.py`.
5. Continuar unicamente con la siguiente fase pendiente, reutilizando la estructura actual.
