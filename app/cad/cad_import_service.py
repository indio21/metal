from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import importlib
import json
from pathlib import Path
import sys

from app.extensions import db
from app.models import DrawingJob, Project, UploadedModel
from app.services.upload_service import UploadStorageError, resolve_uploaded_model_path


class FreeCADUnavailableError(Exception):
    pass


class CADAnalysisError(Exception):
    pass


@dataclass
class CADAnalysisResult:
    backend: str
    bounding_box: dict[str, float]
    dimensions: dict[str, float]
    tentative_scale_factor: float
    tentative_scale_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "bounding_box": self.bounding_box,
            "dimensions": self.dimensions,
            "tentative_scale_factor": self.tentative_scale_factor,
            "tentative_scale_note": self.tentative_scale_note,
        }


class FreeCADAdapter:
    def __init__(self, freecad_lib_path: str | None = None) -> None:
        self.freecad_lib_path = Path(freecad_lib_path) if freecad_lib_path else None

    def analyze_model(self, file_path: Path) -> CADAnalysisResult:
        _freecad_module, part_module = self._load_modules()
        shape = self._read_shape(part_module, file_path)
        bound_box = getattr(shape, "BoundBox", None)

        if bound_box is None:
            raise CADAnalysisError("FreeCAD no devolvio un bounding box valido.")

        x_length = float(getattr(bound_box, "XLength", 0.0))
        y_length = float(getattr(bound_box, "YLength", 0.0))
        z_length = float(getattr(bound_box, "ZLength", 0.0))

        if max(x_length, y_length, z_length) <= 0:
            raise CADAnalysisError("El modelo no expone dimensiones globales validas.")

        return CADAnalysisResult(
            backend="FreeCAD",
            bounding_box={
                "xmin": round(float(getattr(bound_box, "XMin", 0.0)), 3),
                "ymin": round(float(getattr(bound_box, "YMin", 0.0)), 3),
                "zmin": round(float(getattr(bound_box, "ZMin", 0.0)), 3),
                "xmax": round(float(getattr(bound_box, "XMax", 0.0)), 3),
                "ymax": round(float(getattr(bound_box, "YMax", 0.0)), 3),
                "zmax": round(float(getattr(bound_box, "ZMax", 0.0)), 3),
            },
            dimensions={
                "x": round(x_length, 3),
                "y": round(y_length, 3),
                "z": round(z_length, 3),
            },
            tentative_scale_factor=1.0,
            tentative_scale_note="Se conserva la escala nativa del archivo; STEP/IGES no siempre expone unidades consistentes.",
        )

    def _load_modules(self):
        self._prepare_sys_path()
        try:
            freecad_module = importlib.import_module("FreeCAD")
            part_module = importlib.import_module("Part")
        except ImportError as error:
            raise FreeCADUnavailableError(self._build_unavailable_message()) from error
        return freecad_module, part_module

    def _prepare_sys_path(self) -> None:
        if self.freecad_lib_path is None:
            return
        freecad_path = str(self.freecad_lib_path)
        if freecad_path not in sys.path:
            sys.path.insert(0, freecad_path)

    def _read_shape(self, part_module, file_path: Path):
        read_errors: list[str] = []

        if hasattr(part_module, "read"):
            try:
                shape = part_module.read(str(file_path))
                if shape is not None:
                    return shape
            except Exception as error:  # pragma: no cover
                read_errors.append(str(error))

        try:
            shape = part_module.Shape()
            shape.read(str(file_path))
            return shape
        except Exception as error:  # pragma: no cover
            read_errors.append(str(error))

        raise CADAnalysisError(
            "FreeCAD no pudo importar el archivo CAD. " + " / ".join(read_errors[-2:])
        )

    def _build_unavailable_message(self) -> str:
        base_message = (
            "FreeCAD no esta disponible en este entorno. "
            "Instalalo y configura FREECAD_LIB_PATH para habilitar el analisis real."
        )
        if self.freecad_lib_path:
            return f"{base_message} Ruta configurada: {self.freecad_lib_path}"
        return (
            f"{base_message} En Windows suele apuntar a algo como "
            f"'C:\\Program Files\\FreeCAD 0.21\\bin'."
        )


def analyze_project_model(
    *,
    project: Project,
    uploaded_model: UploadedModel,
    upload_root: Path,
    freecad_lib_path: str | None = None,
) -> DrawingJob:
    drawing_job = DrawingJob(
        project_id=project.id,
        template_id=project.template_id,
        uploaded_model_id=uploaded_model.id,
        status="running",
        output_type="model_analysis",
        analyzer_backend="FreeCAD",
        started_at=datetime.utcnow(),
    )
    db.session.add(drawing_job)
    db.session.commit()

    try:
        file_path = resolve_uploaded_model_path(upload_root, uploaded_model)
        adapter = FreeCADAdapter(freecad_lib_path=freecad_lib_path)
        analysis_result = adapter.analyze_model(file_path)
    except (UploadStorageError, FreeCADUnavailableError, CADAnalysisError) as error:
        drawing_job.status = "failed"
        drawing_job.finished_at = datetime.utcnow()
        drawing_job.error_message = str(error)
        drawing_job.analysis_summary = None
        db.session.commit()
        return drawing_job

    drawing_job.status = "completed"
    drawing_job.finished_at = datetime.utcnow()
    drawing_job.error_message = None
    drawing_job.analysis_summary = json.dumps(analysis_result.as_dict())
    drawing_job.analyzer_backend = analysis_result.backend
    project.status = "ready"
    db.session.commit()
    return drawing_job
