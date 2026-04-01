# Metal MVP 2.0

MVP web orientado a piezas torneadas, axiales o de revolucion. Esta iteracion trabaja de forma incremental sobre el repositorio existente y, en este punto, deja resueltas las Fases 4 y 5 de la version 2.0: analisis CAD con clasificacion axial y estrategia de vistas especifica para piezas torneadas.

## Estado actual

El proyecto ya permite:

1. Crear proyectos reales.
2. Registrar datos base de una pieza axial.
3. Subir archivos `.step`, `.stp`, `.iges` o `.igs`.
4. Analizar la pieza y detectar:
   - bounding box
   - dimensiones globales
   - eje dominante
   - indicadores de axialidad
   - clasificacion axial o no concluyente
5. Generar una estrategia de drawing especifica con:
   - vista lateral principal
   - vista de extremo
   - corte longitudinal
6. Visualizar un preview base de esa estrategia en la UI.

## Reinterpretacion incremental del repositorio existente

El repositorio venia de una version previa mas avanzada. Para respetar la continuidad:

- no se rehizo el proyecto desde cero
- no se borraron capacidades correctas
- se extendio la capa CAD existente
- se agrego una capa de estrategia de vistas especializada en `app/drawing`
- la app siguio ejecutable en todo momento

## Stack actual

- Python 3.11
- Flask
- Bootstrap 5
- SQLAlchemy
- SQLite
- python-dotenv
- pytest

La base existente tambien conserva:

- FreeCAD opcional
- TechDraw opcional
- ezdxf
- reportlab
- Ollama opcional

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

```env
APP_ENV=development
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///metal.db
FREECAD_LIB_PATH=C:\Program Files\FreeCAD 0.21\bin
OLLAMA_ENABLED=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## Configuracion CAD

La integracion real con FreeCAD sigue siendo opcional.

Si FreeCAD esta disponible:

- la app intenta importar el STEP/IGES real
- extrae bounding box y dimensiones reales
- calcula el eje dominante y la clasificacion axial

Si FreeCAD no esta disponible:

- la app usa un fallback demo controlado
- estima dimensiones base para no bloquear el flujo
- igual permite clasificar y construir la estrategia de vistas

### Windows

Ejemplo de configuracion:

```powershell
$env:FREECAD_LIB_PATH="C:\Program Files\FreeCAD 0.21\bin"
python init_db.py
python run.py
```

## Flujo actual 2.0

1. Crear proyecto y pieza.
2. Subir STEP o IGES.
3. Ejecutar `Analizar pieza`.
4. Revisar si la pieza fue clasificada como axial o torneada.
5. Ejecutar `Generar estrategia de vistas`.
6. Ver preview base con lateral principal, extremo y corte longitudinal.

## Regla de negocio vigente

- STEP es el formato principal preferido.
- IGES se acepta como alternativa.
- la UI lo indica explicitamente.

## Testing

Ejecutar:

```powershell
pytest
```

## Limitaciones reales en este punto

- la estrategia generada todavia es preliminar
- no hay acotado completo
- no hay exportacion axial final especializada en estas fases
- la clasificacion axial se apoya en indicadores geometricos simples
- el drawing final similar al cliente queda para la siguiente etapa

## Como retomar si se interrumpe

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
3. Activar `.venv`.
4. Ejecutar `pip install -r requirements.txt`.
5. Ejecutar `python init_db.py`.
6. Validar con `pytest`.
7. Levantar la app con `python run.py`.
8. Continuar solo con la siguiente fase pendiente de la version 2.0.
