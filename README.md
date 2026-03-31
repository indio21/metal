# Metal MVP

Base para un MVP web orientado a metalurgica. Esta Fase 3 extiende la app Flask existente con una capa web de gestion mas completa para piezas y proyectos, lista para anexar uploads CAD en la siguiente iteracion.

## Alcance actual

- App Flask funcional con patron app factory
- Configuracion por entorno (`development`, `testing`, `production`)
- Persistencia real con SQLAlchemy y SQLite
- Dashboard con metricas utiles
- CRUD web basico de proyectos/piezas
- Alta, listado, detalle, edicion y borrado controlado
- Manejo amigable de errores 404 y 500
- Templates base opcionales listos para seleccion

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

## Estado funcional de la Fase 3

- Ya podes crear, editar, listar, consultar y eliminar proyectos.
- El dashboard muestra metricas utiles para el seguimiento del flujo.
- La ficha de pieza ya maneja revision, autor y template base opcional.
- Las pantallas de error son amigables y la navegacion es consistente.
- Todavia no hay carga real de archivos STEP/IGES.
- Todavia no hay integracion con FreeCAD, drawing, exportacion ni Ollama.

## Como retomar si se interrumpe

1. Revisar `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
2. Activar `.venv`.
3. Ejecutar `python init_db.py` para asegurar la base.
4. Validar con `pytest`.
5. Levantar la app con `python run.py`.
6. Continuar unicamente con la siguiente fase pendiente, reutilizando la estructura actual.
