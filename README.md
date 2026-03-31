# Metal MVP

Base inicial para un MVP web orientado a metalurgica. Esta Fase 1 deja preparada una aplicacion Flask con estructura modular, SQLite, layout base con Bootstrap y pantallas minimas para dashboard y creacion de proyecto.

## Alcance actual

- App Flask funcional con patron app factory
- Configuracion por entorno (`development`, `testing`, `production`)
- Persistencia preparada con SQLAlchemy y SQLite
- Dashboard inicial
- Pantalla placeholder para creacion de proyectos
- Estructura lista para integrar carga STEP/IGES en la proxima fase

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
config.py
requirements.txt
README.md
CHANGELOG.md
NEXT_STEPS.md
```

## Requisitos

- Python 3.11
- Entorno local con `pip`

## Puesta en marcha

1. Crear y activar un entorno virtual.
2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Copiar variables de entorno si hace falta:

```bash
copy .env.example .env
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

## Estado de continuidad

- La app crea las tablas automaticamente al iniciar.
- No hay todavia carga de archivos CAD, integracion con FreeCAD, drawings ni exportacion.
- `uploads/` y `exports/` ya estan creados para las siguientes fases.

## Como retomar si se interrumpe

1. Revisar `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
2. Verificar que la app siga arrancando con `python run.py`.
3. Continuar unicamente con la siguiente fase pendiente, reutilizando la estructura actual.
