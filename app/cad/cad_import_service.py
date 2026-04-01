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
    is_demo_fallback: bool = False
    dominant_axis: str = "x"
    dominant_axis_length: float = 0.0
    transverse_similarity: float = 0.0
    axial_ratio: float = 0.0
    family_classification: str = "unclassified"
    classification_note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "bounding_box": self.bounding_box,
            "dimensions": self.dimensions,
            "tentative_scale_factor": self.tentative_scale_factor,
            "tentative_scale_note": self.tentative_scale_note,
            "is_demo_fallback": self.is_demo_fallback,
            "dominant_axis": self.dominant_axis,
            "dominant_axis_length": self.dominant_axis_length,
            "transverse_similarity": self.transverse_similarity,
            "axial_ratio": self.axial_ratio,
            "family_classification": self.family_classification,
            "classification_note": self.classification_note,
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

        dimensions = {
            "x": round(x_length, 3),
            "y": round(y_length, 3),
            "z": round(z_length, 3),
        }
        indicators = _build_axial_indicators(dimensions)

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
            dimensions=dimensions,
            tentative_scale_factor=1.0,
            tentative_scale_note="Se conserva la escala nativa del archivo; STEP/IGES no siempre expone unidades consistentes.",
            dominant_axis=indicators["dominant_axis"],
            dominant_axis_length=indicators["dominant_axis_length"],
            transverse_similarity=indicators["transverse_similarity"],
            axial_ratio=indicators["axial_ratio"],
            family_classification=indicators["family_classification"],
            classification_note=indicators["classification_note"],
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
    except FreeCADUnavailableError:
        analysis_result = _build_demo_analysis_result(uploaded_model=uploaded_model, file_path=file_path)
    except (UploadStorageError, CADAnalysisError) as error:
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


def _build_demo_analysis_result(*, uploaded_model: UploadedModel, file_path: Path) -> CADAnalysisResult:
    file_size = max(file_path.stat().st_size, 1)
    name_seed = sum(ord(character) for character in (uploaded_model.original_filename or uploaded_model.stored_filename or "pieza"))
    base_x = 80 + (name_seed % 90)
    base_y = 35 + (file_size % 55)
    base_z = 20 + ((name_seed + file_size) % 40)

    dim_x = round(float(base_x), 3)
    dim_y = round(float(min(base_y, dim_x * 0.75)), 3)
    dim_z = round(float(min(base_z, max(dim_y * 0.8, 18.0))), 3)

    dimensions = {"x": dim_x, "y": dim_y, "z": dim_z}
    indicators = _build_axial_indicators(dimensions)

    return CADAnalysisResult(
        backend="demo_fallback",
        bounding_box={
            "xmin": 0.0,
            "ymin": 0.0,
            "zmin": 0.0,
            "xmax": dim_x,
            "ymax": dim_y,
            "zmax": dim_z,
        },
        dimensions=dimensions,
        tentative_scale_factor=1.0,
        tentative_scale_note=(
            "FreeCAD no esta disponible en este entorno. "
            "Se genero una estimacion demo de dimensiones para destrabar el flujo del MVP."
        ),
        is_demo_fallback=True,
        dominant_axis=indicators["dominant_axis"],
        dominant_axis_length=indicators["dominant_axis_length"],
        transverse_similarity=indicators["transverse_similarity"],
        axial_ratio=indicators["axial_ratio"],
        family_classification=indicators["family_classification"],
        classification_note=indicators["classification_note"],
    )


def _build_axial_indicators(dimensions: dict[str, float]) -> dict[str, float | str]:
    ordered_axes = sorted(dimensions.items(), key=lambda item: item[1], reverse=True)
    dominant_axis, dominant_length = ordered_axes[0]
    transverse = [max(float(value), 1e-6) for _axis, value in ordered_axes[1:]]
    transverse_max = max(transverse)
    transverse_min = min(transverse)
    transverse_mean = sum(transverse) / len(transverse)

    transverse_similarity = round(transverse_min / transverse_max, 3)
    axial_ratio = round(float(dominant_length) / max(transverse_mean, 1e-6), 3)
    is_axial_candidate = axial_ratio >= 1.35 and transverse_similarity >= 0.55

    if is_axial_candidate:
        family_classification = "axial_turned_candidate"
        classification_note = (
            "La pieza presenta un eje dominante y seccion transversal relativamente pareja. "
            "Es compatible con una estrategia axial o torneada."
        )
    else:
        family_classification = "non_axial_or_uncertain"
        classification_note = (
            "La proporcion general no confirma claramente una pieza de revolucion. "
            "Conviene revisar el modelo antes de aplicar una estrategia axial estricta."
        )

    return {
        "dominant_axis": dominant_axis,
        "dominant_axis_length": round(float(dominant_length), 3),
        "transverse_similarity": transverse_similarity,
        "axial_ratio": axial_ratio,
        "family_classification": family_classification,
        "classification_note": classification_note,
    }
