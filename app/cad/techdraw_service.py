from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from uuid import uuid4

from app.cad.cad_import_service import (
    CADAnalysisError,
    FreeCADAdapter,
    FreeCADUnavailableError,
    analyze_project_model,
)
from app.extensions import db
from app.models import DrawingJob, ExportFile, Project, Template, UploadedModel
from app.services.upload_service import UploadStorageError


class DrawingGenerationError(Exception):
    pass


TEMPLATE_SPECS = {
    "industrial-a4": {
        "width": 1123,
        "height": 794,
        "name": "Industrial basico A4",
    },
    "industrial-a3": {
        "width": 1587,
        "height": 1123,
        "name": "Industrial compacto A3",
    },
}


@dataclass
class DrawingGenerationResult:
    backend: str
    scale_label: str
    dimensions: dict[str, float]
    sheet_width: int
    sheet_height: int
    template_name: str
    title_block: dict[str, str]
    preview_format: str = "svg"

    def as_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "scale_label": self.scale_label,
            "dimensions": self.dimensions,
            "sheet_width": self.sheet_width,
            "sheet_height": self.sheet_height,
            "template_name": self.template_name,
            "title_block": self.title_block,
            "preview_format": self.preview_format,
        }


class TechDrawUnavailableError(Exception):
    pass


class TechDrawAdapter:
    def __init__(self, freecad_lib_path: str | None = None) -> None:
        self.freecad_lib_path = freecad_lib_path

    def generate_svg(
        self,
        *,
        project: Project,
        uploaded_model: UploadedModel,
        analysis_data: dict[str, object],
        template: Template,
        export_path: Path,
    ) -> DrawingGenerationResult:
        raise TechDrawUnavailableError(
            "TechDraw no esta disponible en este entorno. Se usara el generador SVG preliminar."
        )


def generate_preliminary_drawing(
    *,
    project: Project,
    uploaded_model: UploadedModel,
    export_root: Path,
    upload_root: Path,
    freecad_lib_path: str | None = None,
) -> DrawingJob:
    template = _resolve_template(project)
    analysis_job = _get_or_create_analysis(
        project=project,
        uploaded_model=uploaded_model,
        upload_root=upload_root,
        freecad_lib_path=freecad_lib_path,
    )
    if analysis_job.status != "completed":
        return _create_failed_drawing_job(
            project=project,
            uploaded_model=uploaded_model,
            template=template,
            message=analysis_job.error_message or "No fue posible analizar el modelo antes de generar el drawing.",
        )

    analysis_data = analysis_job.analysis_data
    if not analysis_data:
        return _create_failed_drawing_job(
            project=project,
            uploaded_model=uploaded_model,
            template=template,
            message="No hay datos de analisis suficientes para generar el drawing preliminar.",
        )

    drawing_job = DrawingJob(
        project_id=project.id,
        template_id=template.id if template else None,
        uploaded_model_id=uploaded_model.id,
        status="running",
        output_type="preliminary_2d",
        analyzer_backend="TechDraw",
        started_at=datetime.utcnow(),
    )
    db.session.add(drawing_job)
    db.session.commit()

    export_dir = export_root / f"project_{project.id}"
    export_dir.mkdir(parents=True, exist_ok=True)
    export_filename = f"drawing_{project.id}_{drawing_job.id}_{uuid4().hex[:8]}.svg"
    export_path = export_dir / export_filename

    try:
        result = _generate_drawing_svg(
            project=project,
            uploaded_model=uploaded_model,
            analysis_data=analysis_data,
            template=template,
            export_path=export_path,
            freecad_lib_path=freecad_lib_path,
        )
    except (DrawingGenerationError, UploadStorageError, CADAnalysisError, FreeCADUnavailableError) as error:
        drawing_job.status = "failed"
        drawing_job.finished_at = datetime.utcnow()
        drawing_job.error_message = str(error)
        drawing_job.analysis_summary = None
        drawing_job.analyzer_backend = "svg_fallback"
        db.session.commit()
        return drawing_job

    export_file = ExportFile(
        project_id=project.id,
        drawing_job_id=drawing_job.id,
        filename=export_filename,
        file_format="svg",
        file_path=str(export_path.relative_to(export_root)),
        status="generated",
    )
    db.session.add(export_file)
    drawing_job.status = "completed"
    drawing_job.finished_at = datetime.utcnow()
    drawing_job.error_message = None
    drawing_job.analysis_summary = __import__("json").dumps(result.as_dict())
    drawing_job.analyzer_backend = result.backend
    db.session.commit()
    return drawing_job


def resolve_export_path(export_root: Path, export_file: ExportFile) -> Path:
    if not export_file.file_path:
        raise DrawingGenerationError("El drawing no tiene un archivo asociado.")

    candidate = (export_root / export_file.file_path).resolve()
    try:
        candidate.relative_to(export_root.resolve())
    except ValueError as error:
        raise DrawingGenerationError("La ruta del drawing almacenado es invalida.") from error

    if not candidate.exists():
        raise DrawingGenerationError("El archivo preview del drawing no existe en disco.")

    return candidate


def _resolve_template(project: Project) -> Template | None:
    if project.template is not None:
        return project.template
    return Template.query.filter_by(is_default=True).order_by(Template.id.asc()).first()


def _get_or_create_analysis(
    *,
    project: Project,
    uploaded_model: UploadedModel,
    upload_root: Path,
    freecad_lib_path: str | None,
) -> DrawingJob:
    existing_job = (
        DrawingJob.query.filter_by(
            project_id=project.id,
            uploaded_model_id=uploaded_model.id,
            output_type="model_analysis",
            status="completed",
        )
        .order_by(DrawingJob.created_at.desc())
        .first()
    )
    if existing_job is not None:
        return existing_job

    return analyze_project_model(
        project=project,
        uploaded_model=uploaded_model,
        upload_root=upload_root,
        freecad_lib_path=freecad_lib_path,
    )


def _create_failed_drawing_job(
    *,
    project: Project,
    uploaded_model: UploadedModel,
    template: Template | None,
    message: str,
) -> DrawingJob:
    drawing_job = DrawingJob(
        project_id=project.id,
        template_id=template.id if template else None,
        uploaded_model_id=uploaded_model.id,
        status="failed",
        output_type="preliminary_2d",
        analyzer_backend="svg_fallback",
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        error_message=message,
    )
    db.session.add(drawing_job)
    db.session.commit()
    return drawing_job


def _generate_drawing_svg(
    *,
    project: Project,
    uploaded_model: UploadedModel,
    analysis_data: dict[str, object],
    template: Template | None,
    export_path: Path,
    freecad_lib_path: str | None,
) -> DrawingGenerationResult:
    techdraw_adapter = TechDrawAdapter(freecad_lib_path=freecad_lib_path)
    try:
        return techdraw_adapter.generate_svg(
            project=project,
            uploaded_model=uploaded_model,
            analysis_data=analysis_data,
            template=template or Template(name="Fallback", code="industrial-a4"),
            export_path=export_path,
        )
    except TechDrawUnavailableError:
        return _generate_svg_fallback(
            project=project,
            uploaded_model=uploaded_model,
            analysis_data=analysis_data,
            template=template,
            export_path=export_path,
        )


def _generate_svg_fallback(
    *,
    project: Project,
    uploaded_model: UploadedModel,
    analysis_data: dict[str, object],
    template: Template | None,
    export_path: Path,
) -> DrawingGenerationResult:
    dimensions = analysis_data.get("dimensions", {})
    if not dimensions:
        raise DrawingGenerationError("No hay dimensiones disponibles para generar el drawing.")

    template_code = template.code if template else "industrial-a4"
    template_spec = TEMPLATE_SPECS.get(template_code, TEMPLATE_SPECS["industrial-a4"])
    width = template_spec["width"]
    height = template_spec["height"]

    dim_x = float(dimensions.get("x", 0.0))
    dim_y = float(dimensions.get("y", 0.0))
    dim_z = float(dimensions.get("z", 0.0))
    max_dim = max(dim_x, dim_y, dim_z)
    if max_dim <= 0:
        raise DrawingGenerationError("Las dimensiones analizadas no son validas para generar el drawing.")

    drawing_area_width = width - 180
    drawing_area_height = height - 220
    scale_factor = min(drawing_area_width / max(dim_x, dim_y, 1.0), drawing_area_height / max(dim_x, dim_z, 1.0), 2.6)
    scale_label = _build_scale_label(scale_factor)

    title_block = {
        "Pieza": project.name,
        "Fecha": datetime.utcnow().strftime("%Y-%m-%d"),
        "Revision": project.revision,
        "Autor": project.author or "Sin autor",
        "Material": project.material or "No definido",
        "Escala": scale_label,
        "Observaciones": project.notes or "Sin observaciones",
    }

    svg_content = _build_svg_sheet(
        width=width,
        height=height,
        project=project,
        uploaded_model=uploaded_model,
        title_block=title_block,
        dimensions={"x": dim_x, "y": dim_y, "z": dim_z},
        scale_factor=scale_factor,
        template_name=template_spec["name"],
    )
    export_path.write_text(svg_content, encoding="utf-8")

    return DrawingGenerationResult(
        backend="svg_fallback",
        scale_label=scale_label,
        dimensions={"x": round(dim_x, 3), "y": round(dim_y, 3), "z": round(dim_z, 3)},
        sheet_width=width,
        sheet_height=height,
        template_name=template_spec["name"],
        title_block=title_block,
    )


def _build_scale_label(scale_factor: float) -> str:
    if scale_factor >= 1:
        return f"{round(scale_factor, 2)}:1"
    inverse = round(1 / scale_factor, 2)
    return f"1:{inverse}"


def _build_svg_sheet(
    *,
    width: int,
    height: int,
    project: Project,
    uploaded_model: UploadedModel,
    title_block: dict[str, str],
    dimensions: dict[str, float],
    scale_factor: float,
    template_name: str,
) -> str:
    margin = 34
    title_height = 140
    drawing_bottom = height - title_height - margin
    front_x = 90
    front_y = 150
    top_x = 90
    top_y = 40
    side_x = 430
    side_y = 150
    iso_x = 760
    iso_y = 90

    front_w = dimensions["x"] * scale_factor
    front_h = dimensions["z"] * scale_factor
    top_w = dimensions["x"] * scale_factor
    top_h = dimensions["y"] * scale_factor
    side_w = dimensions["y"] * scale_factor
    side_h = dimensions["z"] * scale_factor

    iso_w = dimensions["x"] * scale_factor * 0.72
    iso_h = dimensions["z"] * scale_factor * 0.72
    iso_d = dimensions["y"] * scale_factor * 0.42

    fields = []
    start_x = margin + 14
    start_y = height - title_height + 30
    for index, (label, value) in enumerate(title_block.items()):
        x = start_x + (index % 2) * 300
        y = start_y + (index // 2) * 24
        fields.append(
            f'<text x="{x}" y="{y}" class="tb-label">{escape(label)}:</text>'
            f'<text x="{x + 84}" y="{y}" class="tb-value">{escape(value)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .sheet {{ fill: #fff; stroke: #14213d; stroke-width: 2; }}
    .thin {{ stroke: #3d4b63; stroke-width: 1.5; fill: none; }}
    .dim {{ stroke: #6b7280; stroke-width: 1.1; fill: none; marker-start: url(#arrow); marker-end: url(#arrow); }}
    .view-label {{ font: 600 18px Arial, sans-serif; fill: #14213d; }}
    .title {{ font: 700 22px Arial, sans-serif; fill: #14213d; }}
    .meta {{ font: 500 13px Arial, sans-serif; fill: #334155; }}
    .tb-label {{ font: 700 12px Arial, sans-serif; fill: #334155; }}
    .tb-value {{ font: 500 12px Arial, sans-serif; fill: #111827; }}
    .dim-text {{ font: 600 12px Arial, sans-serif; fill: #334155; }}
  </style>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
      <path d="M0,4 L8,0 L8,8 z" fill="#6b7280" />
    </marker>
  </defs>
  <rect x="{margin}" y="{margin}" width="{width - margin * 2}" height="{height - margin * 2}" class="sheet" rx="12" />
  <line x1="{margin}" y1="{height - title_height}" x2="{width - margin}" y2="{height - title_height}" class="thin" />
  <rect x="{margin}" y="{height - title_height}" width="{width - margin * 2}" height="{title_height}" class="thin" />
  <text x="{margin + 18}" y="{margin + 24}" class="title">Drawing preliminar 2D - {escape(project.name)}</text>
  <text x="{margin + 18}" y="{margin + 48}" class="meta">Template: {escape(template_name)} | Archivo: {escape(uploaded_model.original_filename or uploaded_model.stored_filename or 'Sin archivo')}</text>
  <text x="{margin + 18}" y="{margin + 68}" class="meta">Vistas: frontal, superior, lateral e isometrica</text>

  <text x="{top_x}" y="{top_y - 14}" class="view-label">Vista superior</text>
  <rect x="{top_x}" y="{top_y}" width="{top_w}" height="{top_h}" class="thin" rx="4" />
  <line x1="{top_x}" y1="{top_y + top_h + 22}" x2="{top_x + top_w}" y2="{top_y + top_h + 22}" class="dim" />
  <text x="{top_x + top_w / 2 - 16}" y="{top_y + top_h + 16}" class="dim-text">{round(dimensions["x"], 2)}</text>

  <text x="{front_x}" y="{front_y - 14}" class="view-label">Vista frontal</text>
  <rect x="{front_x}" y="{front_y}" width="{front_w}" height="{front_h}" class="thin" rx="4" />
  <line x1="{front_x}" y1="{front_y + front_h + 28}" x2="{front_x + front_w}" y2="{front_y + front_h + 28}" class="dim" />
  <line x1="{front_x - 24}" y1="{front_y}" x2="{front_x - 24}" y2="{front_y + front_h}" class="dim" />
  <text x="{front_x + front_w / 2 - 16}" y="{front_y + front_h + 22}" class="dim-text">{round(dimensions["x"], 2)}</text>
  <text x="{front_x - 56}" y="{front_y + front_h / 2}" class="dim-text">{round(dimensions["z"], 2)}</text>

  <text x="{side_x}" y="{side_y - 14}" class="view-label">Vista lateral</text>
  <rect x="{side_x}" y="{side_y}" width="{side_w}" height="{side_h}" class="thin" rx="4" />
  <line x1="{side_x}" y1="{side_y + side_h + 28}" x2="{side_x + side_w}" y2="{side_y + side_h + 28}" class="dim" />
  <text x="{side_x + side_w / 2 - 16}" y="{side_y + side_h + 22}" class="dim-text">{round(dimensions["y"], 2)}</text>

  <text x="{iso_x}" y="{iso_y - 14}" class="view-label">Vista isometrica</text>
  <polygon points="{iso_x},{iso_y + iso_d} {iso_x + iso_w},{iso_y} {iso_x + iso_w + iso_d},{iso_y + iso_d} {iso_x + iso_d},{iso_y + iso_d * 2}" class="thin" />
  <polygon points="{iso_x + iso_d},{iso_y + iso_d * 2} {iso_x + iso_w + iso_d},{iso_y + iso_d} {iso_x + iso_w + iso_d},{iso_y + iso_d + iso_h} {iso_x + iso_d},{iso_y + iso_d * 2 + iso_h}" class="thin" />
  <polygon points="{iso_x},{iso_y + iso_d} {iso_x + iso_d},{iso_y + iso_d * 2} {iso_x + iso_d},{iso_y + iso_d * 2 + iso_h} {iso_x},{iso_y + iso_d + iso_h}" class="thin" />

  {''.join(fields)}
</svg>"""
