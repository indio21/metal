from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

from app.cad.cad_import_service import analyze_project_model
from app.extensions import db
from app.models import DrawingJob, Project, UploadedModel


class DrawingStrategyError(Exception):
    pass


@dataclass
class AxialViewDefinition:
    key: str
    label: str
    width: float
    height: float
    notes: str

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "label": self.label,
            "width": round(self.width, 3),
            "height": round(self.height, 3),
            "notes": self.notes,
        }


@dataclass
class DrawingStrategyResult:
    family: str
    dominant_axis: str
    axial_ratio: float
    transverse_similarity: float
    accepted: bool
    layout_name: str
    notes: list[str]
    views: list[AxialViewDefinition]
    svg_preview: str

    def as_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "dominant_axis": self.dominant_axis,
            "axial_ratio": self.axial_ratio,
            "transverse_similarity": self.transverse_similarity,
            "accepted": self.accepted,
            "layout_name": self.layout_name,
            "notes": self.notes,
            "views": [view.as_dict() for view in self.views],
            "svg_preview": self.svg_preview,
        }


def generate_axial_drawing_strategy(
    *,
    project: Project,
    uploaded_model: UploadedModel,
    upload_root: Path,
    freecad_lib_path: str | None = None,
) -> DrawingJob:
    analysis_job = _get_or_create_analysis(
        project=project,
        uploaded_model=uploaded_model,
        upload_root=upload_root,
        freecad_lib_path=freecad_lib_path,
    )
    if analysis_job.status != "completed":
        return _create_failed_strategy_job(
            project=project,
            uploaded_model=uploaded_model,
            message=analysis_job.error_message or "No fue posible analizar la pieza antes de construir la estrategia.",
        )

    analysis_data = analysis_job.analysis_data
    if not analysis_data:
        return _create_failed_strategy_job(
            project=project,
            uploaded_model=uploaded_model,
            message="No hay datos de analisis suficientes para construir la estrategia axial.",
        )

    strategy_job = DrawingJob(
        project_id=project.id,
        template_id=project.template_id,
        uploaded_model_id=uploaded_model.id,
        status="running",
        output_type="axial_strategy",
        analyzer_backend="axial_strategy_service",
        started_at=datetime.utcnow(),
    )
    db.session.add(strategy_job)
    db.session.commit()

    try:
        strategy = build_axial_strategy(project=project, analysis_data=analysis_data)
    except DrawingStrategyError as error:
        strategy_job.status = "failed"
        strategy_job.finished_at = datetime.utcnow()
        strategy_job.error_message = str(error)
        strategy_job.analysis_summary = None
        db.session.commit()
        return strategy_job

    strategy_job.status = "completed"
    strategy_job.finished_at = datetime.utcnow()
    strategy_job.error_message = None
    strategy_job.analysis_summary = json.dumps(strategy.as_dict())
    db.session.commit()
    return strategy_job


def build_axial_strategy(*, project: Project, analysis_data: dict[str, object]) -> DrawingStrategyResult:
    family = str(analysis_data.get("family_classification") or "unclassified")
    if not family.startswith("axial"):
        raise DrawingStrategyError(
            "La pieza no quedo clasificada como axial o torneada. Revisa el modelo antes de aplicar esta estrategia."
        )

    dimensions = analysis_data.get("dimensions", {})
    dominant_axis = str(analysis_data.get("dominant_axis") or "x")
    long_dim, radial_major, radial_minor = _resolve_orientation(dimensions, dominant_axis)

    views = [
        AxialViewDefinition(
            key="lateral",
            label="Vista lateral principal",
            width=long_dim,
            height=radial_major,
            notes="Perfil longitudinal exterior de la pieza sobre el eje dominante.",
        ),
        AxialViewDefinition(
            key="extremo",
            label="Vista de extremo",
            width=radial_major,
            height=radial_major,
            notes="Circulos concentricos y ejes de centro segun el diametro exterior estimado.",
        ),
        AxialViewDefinition(
            key="corte_longitudinal",
            label="Corte longitudinal",
            width=long_dim,
            height=radial_major,
            notes="Seccion longitudinal con rayado para mostrar interior util y escalones axiales.",
        ),
    ]

    svg_preview = _build_strategy_svg(
        project=project,
        dominant_axis=dominant_axis,
        long_dim=long_dim,
        radial_major=radial_major,
        radial_minor=radial_minor,
    )

    return DrawingStrategyResult(
        family=family,
        dominant_axis=dominant_axis,
        axial_ratio=float(analysis_data.get("axial_ratio") or 0.0),
        transverse_similarity=float(analysis_data.get("transverse_similarity") or 0.0),
        accepted=True,
        layout_name="axial_three_view_layout",
        notes=[
            "Vista lateral principal como vista dominante.",
            "Vista de extremo con ejes de centro.",
            "Corte longitudinal sin isometrica.",
            "Layout base similar a plano de taller axial.",
        ],
        views=views,
        svg_preview=svg_preview,
    )


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


def _create_failed_strategy_job(*, project: Project, uploaded_model: UploadedModel, message: str) -> DrawingJob:
    strategy_job = DrawingJob(
        project_id=project.id,
        template_id=project.template_id,
        uploaded_model_id=uploaded_model.id,
        status="failed",
        output_type="axial_strategy",
        analyzer_backend="axial_strategy_service",
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        error_message=message,
    )
    db.session.add(strategy_job)
    db.session.commit()
    return strategy_job


def _resolve_orientation(dimensions: dict[str, object], dominant_axis: str) -> tuple[float, float, float]:
    axis_map = {axis: float(dimensions.get(axis, 0.0) or 0.0) for axis in ("x", "y", "z")}
    long_dim = axis_map.get(dominant_axis, 0.0)
    radial_axes = [axis for axis in ("x", "y", "z") if axis != dominant_axis]
    radial_values = [axis_map[axis] for axis in radial_axes]
    radial_major = max(radial_values) if radial_values else 0.0
    radial_minor = min(radial_values) if radial_values else radial_major
    return long_dim, radial_major, radial_minor


def _build_strategy_svg(
    *,
    project: Project,
    dominant_axis: str,
    long_dim: float,
    radial_major: float,
    radial_minor: float,
) -> str:
    sheet_width = 1080
    sheet_height = 640
    margin = 36
    usable_width = sheet_width - margin * 2
    usable_height = sheet_height - margin * 2

    long_scale = max(long_dim, 1.0)
    radial_scale = max(radial_major, radial_minor, 1.0)
    scale = min(420 / long_scale, 130 / radial_scale, 2.5)

    side_width = long_dim * scale
    side_height = radial_major * scale
    end_diameter = radial_major * scale
    section_width = long_dim * scale
    section_height = radial_major * scale

    side_x = 68
    side_y = 150
    end_center_x = 700
    end_center_y = 220
    section_x = 68
    section_y = 390

    hatch_lines = []
    line_step = 16
    current = 0
    while current <= section_width + section_height:
        x1 = section_x + max(current - section_height, 0)
        y1 = section_y + min(current, section_height)
        x2 = section_x + min(current, section_width)
        y2 = section_y + max(current - section_width, 0)
        hatch_lines.append(
            f'<line x1="{round(x1, 2)}" y1="{round(y1, 2)}" x2="{round(x2, 2)}" y2="{round(y2, 2)}" class="hatch" />'
        )
        current += line_step

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{sheet_width}" height="{sheet_height}" viewBox="0 0 {sheet_width} {sheet_height}">
  <style>
    .frame {{ fill: #fff; stroke: #1f2937; stroke-width: 2; }}
    .shape {{ fill: none; stroke: #0f172a; stroke-width: 2; }}
    .center {{ stroke: #64748b; stroke-width: 1.2; stroke-dasharray: 8 6; }}
    .hatch {{ stroke: #94a3b8; stroke-width: 1; }}
    .title {{ font: 700 22px Arial, sans-serif; fill: #0f172a; }}
    .label {{ font: 600 15px Arial, sans-serif; fill: #1f2937; }}
    .meta {{ font: 500 12px Arial, sans-serif; fill: #475569; }}
  </style>
  <rect x="{margin}" y="{margin}" width="{usable_width}" height="{usable_height}" rx="12" class="frame" />
  <text x="60" y="74" class="title">Estrategia axial preliminar - {escape(project.resolved_part_name)}</text>
  <text x="60" y="98" class="meta">Layout previsto: vista lateral principal, vista de extremo y corte longitudinal</text>
  <text x="60" y="118" class="meta">Eje dominante detectado: {escape(dominant_axis.upper())}</text>

  <text x="{side_x}" y="{side_y - 18}" class="label">Vista lateral principal</text>
  <rect x="{side_x}" y="{side_y}" width="{round(side_width, 2)}" height="{round(side_height, 2)}" rx="8" class="shape" />
  <line x1="{side_x}" y1="{side_y + side_height / 2}" x2="{side_x + side_width}" y2="{side_y + side_height / 2}" class="center" />

  <text x="{end_center_x - 65}" y="{side_y - 18}" class="label">Vista de extremo</text>
  <circle cx="{end_center_x}" cy="{end_center_y}" r="{round(end_diameter / 2, 2)}" class="shape" />
  <circle cx="{end_center_x}" cy="{end_center_y}" r="{round(max(end_diameter * 0.28, 14), 2)}" class="shape" />
  <line x1="{end_center_x - end_diameter / 2 - 24}" y1="{end_center_y}" x2="{end_center_x + end_diameter / 2 + 24}" y2="{end_center_y}" class="center" />
  <line x1="{end_center_x}" y1="{end_center_y - end_diameter / 2 - 24}" x2="{end_center_x}" y2="{end_center_y + end_diameter / 2 + 24}" class="center" />

  <text x="{section_x}" y="{section_y - 18}" class="label">Corte longitudinal</text>
  <rect x="{section_x}" y="{section_y}" width="{round(section_width, 2)}" height="{round(section_height, 2)}" rx="8" class="shape" />
  {''.join(hatch_lines)}
  <line x1="{section_x}" y1="{section_y + section_height / 2}" x2="{section_x + section_width}" y2="{section_y + section_height / 2}" class="center" />
</svg>"""
