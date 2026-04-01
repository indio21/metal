# Metal MVP 2.0

MVP web orientado a piezas torneadas, axiales o de revolucion. Esta iteracion trabaja de forma incremental sobre el repositorio existente y, en este punto, deja cerrada la Fase 8 de la version 2.0: IA opcional con Ollama, tests y documentacion final.

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
6. Generar una hoja axial preliminar con:
   - marco exterior
   - cajetin tecnico
   - notas generales
   - linea de centro
   - cotas basicas de longitudes axiales y diametros
   - llamada simple para radio y chaflan
7. Visualizar preview SVG directamente en navegador.
8. Exportar PDF vectorial y DXF editable.
9. Consultar historial de exportaciones por proyecto.
10. Pedir asistencia opcional para:
   - sugerir nombre tecnico
   - sugerir material o tratamiento
   - advertir faltantes del cajetin
   - explicar las vistas generadas

## Reinterpretacion incremental del repositorio existente

El repositorio venia de una version previa mas avanzada. Para respetar la continuidad:

- no se rehizo el proyecto desde cero
- no se borraron capacidades correctas
- se extendio la capa CAD existente
- se agrego una capa de estrategia de vistas y hoja axial especializada en `app/drawing`
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
.\.venv\Scripts\python.exe init_db.py
```

### 4. Ejecutar la app

```powershell
.\.venv\Scripts\python.exe run.py
```

Abrir `http://127.0.0.1:5000`.

## Instalacion rapida desde cero

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe init_db.py
.\.venv\Scripts\python.exe run.py
```

## Variables de entorno

```env
APP_ENV=development
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///metal.db
FREECAD_LIB_PATH=C:\Program Files\FreeCAD 0.21\bin
DEFAULT_TOLERANCE_NOTE=Salvo indicacion contraria: tolerancia general ISO 2768-m.
DEFAULT_EDGE_NOTE=Eliminar cantos vivos y rebabas. Romper aristas 0.2-0.5 mm.
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
.\.venv\Scripts\python.exe init_db.py
.\.venv\Scripts\python.exe run.py
```

## Configuracion de Ollama

Ollama es opcional. La app debe seguir funcionando aunque no este instalado.

### Si no queres usar Ollama

```env
OLLAMA_ENABLED=false
```

La UI sigue disponible y la app responde con ayuda local.

### Si queres usar Ollama

1. Instalar Ollama localmente.
2. Levantar el servicio de Ollama.
3. Descargar un modelo local, por ejemplo:

```powershell
ollama pull llama3.2
```

4. Configurar:

```env
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Casos de uso actuales:

- sugerir nombre tecnico de pieza
- sugerir material o tratamiento si faltan campos
- advertir faltantes del cajetin
- explicar que vistas genero la app y por que

## Flujo actual 2.0

1. Crear proyecto y pieza.
2. Subir STEP o IGES.
3. Ejecutar `Analizar pieza`.
4. Revisar si la pieza fue clasificada como axial o torneada.
5. Ejecutar `Generar estrategia de vistas`.
6. Ejecutar `Generar hoja axial`.
7. Revisar preview SVG con lateral principal, extremo y corte longitudinal.
8. Exportar a PDF o DXF.
9. Usar asistencia opcional si queres completar datos o revisar el resultado.

## Regla de negocio vigente

- STEP es el formato principal preferido.
- IGES se acepta como alternativa.
- la UI lo indica explicitamente.

## Testing

Ejecutar:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Limitaciones reales en este punto

- el acotado sigue siendo basico y heuristico
- la hoja sigue siendo preliminar y editable fuera de la app
- la clasificacion axial se apoya en indicadores geometricos simples
- no hay GD&T completo ni deteccion universal de features torneadas
- la ayuda con Ollama no dibuja ni acota; solo asiste con texto
- FreeCAD sigue siendo opcional y el fallback demo prioriza continuidad sobre exactitud

## Resultado esperado del MVP 2.0

- app web navegable
- carga STEP/IGES
- analisis y clasificacion axial
- plano automatico preliminar con tres vistas especializadas
- cajetin y notas generales
- preview SVG y exportaciones PDF/DXF
- asistencia IA opcional sin dependencia obligatoria

## Proximos pasos sugeridos

- refinar la similitud visual con el ejemplo del cliente
- mejorar deteccion de escalones, radios y chaflanes reales
- fortalecer el corte longitudinal con interior mas fiel
- preparar una etapa de revision manual o reglas mas finas de taller

## Como retomar si se interrumpe

1. Inspeccionar primero la estructura actual del repositorio.
2. Leer `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
3. Activar `.venv`.
4. Ejecutar `pip install -r requirements.txt`.
5. Ejecutar `.\.venv\Scripts\python.exe init_db.py`.
6. Validar con `.\.venv\Scripts\python.exe -m pytest`.
7. Levantar la app con `.\.venv\Scripts\python.exe run.py`.
8. Continuar solo con la siguiente fase pendiente de la version 2.0.
