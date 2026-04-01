# Metal MVP

MVP web para metalurgica orientado a piezas individuales. El proyecto permite gestionar piezas, subir archivos STEP/IGES, ejecutar un analisis CAD base, generar un drawing preliminar 2D, visualizar un preview web, exportar PDF/DXF y usar asistencia opcional con Ollama sin volverla obligatoria.

## Estado del MVP

El flujo principal navegable ya esta implementado:

1. Crear proyecto de pieza.
2. Completar datos base.
3. Subir un archivo `.step`, `.stp`, `.iges` o `.igs`.
4. Analizar el modelo.
5. Generar un drawing preliminar 2D.
6. Ver preview SVG.
7. Exportar a PDF y DXF.
8. Usar ayuda opcional con Ollama o fallback local.

## Stack

- Python 3.11
- Flask
- Bootstrap 5
- SQLAlchemy
- SQLite
- python-dotenv
- pytest
- FreeCAD opcional
- TechDraw opcional
- ezdxf
- reportlab
- Ollama opcional

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

## Instalacion completa

### 1. Crear y activar entorno virtual

```powershell
python -m venv .venv
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

La app funciona sin `.env`, pero se puede personalizar copiando `.env.example`:

```env
APP_ENV=development
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///metal.db
FREECAD_LIB_PATH=C:\Program Files\FreeCAD 0.21\bin
OLLAMA_ENABLED=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## Configuracion de FreeCAD

FreeCAD sigue siendo opcional. Si no esta instalado:

- la app sigue levantando
- el upload sigue funcionando
- el analisis muestra fallback controlado si no puede ejecutarse
- el drawing usa arquitectura equivalente con preview SVG

### Windows

1. Instalar FreeCAD.
2. Identificar la carpeta con los modulos Python de FreeCAD.
3. Configurar `FREECAD_LIB_PATH`, por ejemplo:

```powershell
$env:FREECAD_LIB_PATH="C:\Program Files\FreeCAD 0.21\bin"
```

4. Reiniciar la terminal.
5. Ejecutar:

```powershell
python init_db.py
python run.py
```

Si `FREECAD_LIB_PATH` no apunta a una instalacion valida, la app usa su fallback controlado y mantiene el flujo navegable.

## Configuracion de Ollama

La integracion con Ollama es opcional y desacoplada. Si Ollama no esta disponible, la app sigue funcionando y muestra ayuda local.

### Variables necesarias

- `OLLAMA_ENABLED=true`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_MODEL=llama3.2`

### Ejemplo en PowerShell

```powershell
$env:OLLAMA_ENABLED="true"
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:OLLAMA_MODEL="llama3.2"
python run.py
```

### Casos de uso soportados

- sugerir nombre tecnico de pieza
- sugerir descripcion
- advertir campos faltantes
- ayudar a completar cajetin
- explicar que genero la app

Si Ollama no responde o esta desactivado, el detalle del proyecto muestra una respuesta local en lugar de cortar el flujo.

## Exportacion y preview

- El preview web se guarda como SVG.
- La exportacion a PDF usa `reportlab`.
- La exportacion a DXF usa `ezdxf`.
- Los archivos se guardan en `/exports`.
- La metadata queda registrada en `ExportFile`.

## Testing

Ejecutar:

```powershell
pytest
```

Cobertura actual basica:

- creacion de proyecto
- validacion de archivos permitidos y no permitidos
- subida de archivo
- endpoints principales
- analisis y drawing preliminar
- exportacion PDF y DXF
- fallback de Ollama
- respuesta mockeada de Ollama

## Limitaciones reales del MVP

- Solo trabaja con piezas individuales.
- No soporta ensamblajes.
- No implementa BOM ni balloons.
- No promete acotado universal ni layout final perfecto.
- La integracion profunda con FreeCAD/TechDraw depende del entorno local.
- El drawing generado es preliminar y sirve como base operativa, no como plano definitivo universal.
- Ollama es totalmente opcional.

## Como retomar si se interrumpe

1. Revisar `README.md`, `CHANGELOG.md` y `NEXT_STEPS.md`.
2. Activar `.venv`.
3. Ejecutar `pip install -r requirements.txt`.
4. Verificar `FREECAD_LIB_PATH` si queres usar integracion local de FreeCAD.
5. Verificar `OLLAMA_ENABLED`, `OLLAMA_BASE_URL` y `OLLAMA_MODEL` si queres asistencia IA.
6. Ejecutar `python init_db.py`.
7. Validar con `pytest`.
8. Levantar la app con `python run.py`.

## Proximos pasos sugeridos

- mejorar integracion real con FreeCAD y TechDraw
- enriquecer templates y cajetin editable
- mejorar cotas principales
- separar mejor preview web vs salida final
- agregar cola de jobs si el flujo crece
- sumar asistencia IA mas contextual sin volverla obligatoria
