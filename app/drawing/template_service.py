from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from uuid import uuid4

from app.drawing.dimensioning_service import DimensioningError, build_axial_dimensioning
from app.drawing.drawing_strategy_service import generate_axial_drawing_strategy
from app.extensions import db
from app.models import DrawingJob, ExportFile, Project, Template, UploadedModel


SHEET_SPECS = {
    "industrial-a4": {"width": 1280, "height": 900, "name": "Industrial basico A4"},
    "industrial-a3": {"width": 1580, "height": 1120, "name": "Industrial compacto A3"},
}


class AxialSheetError(Exception):
    pass


@dataclass
class AxialSheetResult:
    backend: str
    template_name: str
    sheet_width: int
    sheet_height: int
    scale_label: str
    title_block: dict[str, str]
    notes: list[str]
    dimension_plan: dict[str, object]
    view_layout: dict[str, object]
    svg_preview: str

    def as_dict(self) -> dict[str, object]:
        return {
            "sheet_type": "axial_turned_sheet",
            "backend": self.backend,
            "template_name": self.template_name,
            "sheet_width": self.sheet_width,
            "sheet_height": self.sheet_height,
            "scale_label": self.scale_label,
            "title_block": self.title_block,
            "notes": self.notes,
            "dimension_plan": self.dimension_plan,
            "view_layout": self.view_layout,
            "svg_preview": self.svg_preview,
        }


def generate_axial_technical_sheet(
    *,
    project: Project,
    uploaded_model: UploadedModel,
    export_root: Path,
    upload_root: Path,
    freecad_lib_path: str | None = None,
    default_tolerance_note: str = "Salvo indicacion contraria: tolerancia general ISO 2768-m.",
    default_edge_note: str = "Eliminar cantos vivos y rebabas. Romper aristas 0.2-0.5 mm.",
) -> DrawingJob:
    strategy_job = _get_or_create_strategy(
        project=project,
        uploaded_model=uploaded_model,
        upload_root=upload_root,
        freecad_lib_path=freecad_lib_path,
    )
    if strategy_job.status != "completed":
        return _create_failed_sheet_job(project=project, uploaded_model=uploaded_model, message=strategy_job.error_message or "No fue posible generar la estrategia axial.")

    analysis_job = _get_completed_analysis(project=project, uploaded_model=uploaded_model)
    if analysis_job is None:
        return _create_failed_sheet_job(project=project, uploaded_model=uploaded_model, message="No hay analisis CAD disponible para construir la hoja axial.")

    template = _resolve_template(project)
    sheet_job = DrawingJob(
        project_id=project.id,
        template_id=template.id if template else None,
        uploaded_model_id=uploaded_model.id,
        status="running",
        output_type="axial_sheet",
        analyzer_backend="axial_template_service",
        started_at=datetime.utcnow(),
    )
    db.session.add(sheet_job)
    db.session.commit()

    try:
        result = build_axial_sheet_result(
            project=project,
            template=template,
            analysis_data=analysis_job.analysis_data,
            default_tolerance_note=default_tolerance_note,
            default_edge_note=default_edge_note,
        )
    except (AxialSheetError, DimensioningError) as error:
        sheet_job.status = "failed"
        sheet_job.finished_at = datetime.utcnow()
        sheet_job.error_message = str(error)
        db.session.commit()
        return sheet_job

    export_dir = export_root / f"project_{project.id}"
    export_dir.mkdir(parents=True, exist_ok=True)
    svg_name = f"axial_sheet_{project.id}_{sheet_job.id}_{uuid4().hex[:8]}.svg"
    svg_path = export_dir / svg_name
    svg_path.write_text(result.svg_preview, encoding="utf-8")

    preview_export = ExportFile(
        project_id=project.id,
        drawing_job_id=sheet_job.id,
        filename=svg_name,
        file_format="svg",
        file_path=str(svg_path.relative_to(export_root)),
        status="generated",
    )
    db.session.add(preview_export)
    sheet_job.status = "completed"
    sheet_job.finished_at = datetime.utcnow()
    sheet_job.error_message = None
    sheet_job.analysis_summary = json.dumps(result.as_dict())
    db.session.commit()
    return sheet_job


def build_axial_sheet_result(
    *,
    project: Project,
    template: Template | None,
    analysis_data: dict[str, object],
    default_tolerance_note: str,
    default_edge_note: str,
) -> AxialSheetResult:
    family = str(analysis_data.get("family_classification") or "")
    if not family.startswith("axial"):
        raise AxialSheetError("La pieza no quedo clasificada como axial o torneada.")

    dimension_plan = build_axial_dimensioning(
        project=project,
        analysis_data=analysis_data,
        default_tolerance_note=default_tolerance_note,
        default_edge_note=default_edge_note,
    )
    template_spec = _resolve_template_spec(template)
    scale_factor = min(540 / max(float(dimension_plan["overall_length"]), 1.0), 160 / max(float(dimension_plan["outer_diameter"]), 1.0), 3.0)
    scale_label = _build_scale_label(scale_factor)
    title_block = _build_title_block(project, scale_label)
    view_layout = _build_view_layout(template_spec, dimension_plan, scale_factor)
    svg_preview = render_axial_sheet_svg(
        project=project,
        template_name=template_spec["name"],
        title_block=title_block,
        notes=dimension_plan["general_notes"],
        dimension_plan=dimension_plan,
        view_layout=view_layout,
        sheet_width=template_spec["width"],
        sheet_height=template_spec["height"],
    )
    return AxialSheetResult(
        backend="axial_template_service",
        template_name=template_spec["name"],
        sheet_width=template_spec["width"],
        sheet_height=template_spec["height"],
        scale_label=scale_label,
        title_block=title_block,
        notes=list(dimension_plan["general_notes"]),
        dimension_plan=dimension_plan,
        view_layout=view_layout,
        svg_preview=svg_preview,
    )


def render_axial_sheet_svg(
    *,
    project: Project,
    template_name: str,
    title_block: dict[str, str],
    notes: list[str],
    dimension_plan: dict[str, object],
    view_layout: dict[str, object],
    sheet_width: int,
    sheet_height: int,
) -> str:
    side = view_layout["side"]
    end = view_layout["end"]
    section = view_layout["section"]
    title = view_layout["title_block"]
    notes_box = view_layout["notes_box"]
    margin = view_layout["frame"]["margin"]
    svg_notes = "".join(
        f'<text x="{notes_box["x"] + 16}" y="{notes_box["y"] + 34 + index * 22}" class="note-text">{escape(note)}</text>'
        for index, note in enumerate(notes)
    )
    svg_title = "".join(
        f'<text x="{title["x"] + 16 + (index % 2) * (title["width"] / 2)}" y="{title["y"] + title["height"] - 22 - (index // 2) * 20}" class="tb-text">{escape(label)}: {escape(str(value))}</text>'
        for index, (label, value) in enumerate(title_block.items())
    )
    side_rects = "".join(_svg_rectangles(side["x"], side["center_y"], side["sections"]))
    section_rects = "".join(_svg_rectangles(section["x"], section["center_y"], section["segments"]))
    hatch_lines = "".join(_svg_hatch(section["x"], section["y"], section["width"], section["outer_height"]))
    top_dims = []
    current_x = side["x"]
    for index, segment in enumerate(side["sections"]):
        y = side["y"] - 30 - index * 18
        top_dims.append(_svg_dim_h(current_x, current_x + segment["length_px"], y, f'{segment["label"]} {segment["length"]}'))
        current_x += segment["length_px"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{sheet_width}" height="{sheet_height}" viewBox="0 0 {sheet_width} {sheet_height}">
  <style>
    .sheet {{ fill: #fff; stroke: #14213d; stroke-width: 2; }}
    .light {{ fill: none; stroke: #94a3b8; stroke-width: 1.1; }}
    .shape {{ fill: none; stroke: #0f172a; stroke-width: 2; }}
    .center {{ stroke: #64748b; stroke-width: 1.1; stroke-dasharray: 8 6; }}
    .hatch {{ stroke: #cbd5e1; stroke-width: 1; }}
    .title {{ font: 700 24px Arial, sans-serif; fill: #0f172a; }}
    .subtitle {{ font: 500 13px Arial, sans-serif; fill: #475569; }}
    .view-label {{ font: 700 15px Arial, sans-serif; fill: #0f172a; }}
    .tb-text {{ font: 500 11px Arial, sans-serif; fill: #334155; }}
    .note-text {{ font: 500 12px Arial, sans-serif; fill: #334155; }}
    .dim, .leader {{ stroke: #475569; stroke-width: 1.1; fill: none; marker-start: url(#arrow); marker-end: url(#arrow); }}
    .leader-single {{ stroke: #475569; stroke-width: 1.1; fill: none; marker-end: url(#arrow); }}
    .dim-text {{ font: 700 11px Arial, sans-serif; fill: #334155; }}
  </style>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#475569" />
    </marker>
  </defs>
  <rect x="{margin}" y="{margin}" width="{sheet_width - margin * 2}" height="{sheet_height - margin * 2}" rx="12" class="sheet" />
  <rect x="{margin + 12}" y="{margin + 12}" width="{sheet_width - (margin + 12) * 2}" height="{sheet_height - (margin + 12) * 2}" rx="8" class="light" />
  <line x1="{margin}" y1="{title["y"]}" x2="{sheet_width - margin}" y2="{title["y"]}" class="light" />
  <rect x="{title["x"]}" y="{title["y"]}" width="{title["width"]}" height="{title["height"]}" class="light" />
  <rect x="{notes_box["x"]}" y="{notes_box["y"]}" width="{notes_box["width"]}" height="{notes_box["height"]}" rx="8" class="light" />
  <text x="{margin + 20}" y="{margin + 28}" class="title">{escape(project.resolved_part_name)}</text>
  <text x="{margin + 20}" y="{margin + 52}" class="subtitle">Hoja axial preliminar - {escape(template_name)} - unidades en mm</text>
  <text x="{margin + 20}" y="{margin + 72}" class="subtitle">Vista lateral principal, vista de extremo y corte longitudinal. Exportacion vectorial real.</text>
  <text x="{side["x"]}" y="{side["y"] - 16}" class="view-label">Vista lateral principal</text>
  {side_rects}
  <line x1="{side["x"] - 18}" y1="{side["center_y"]}" x2="{side["x"] + side["width"] + 18}" y2="{side["center_y"]}" class="center" />
  {''.join(top_dims)}
  {_svg_dim_h(side["x"], side["x"] + side["width"], side["y"] + side["outer_height"] + 48, f'L total {dimension_plan["overall_length"]}')}
  {_svg_dim_v(side["x"] + side["width"] + 54, side["center_y"] - side["outer_height"] / 2, side["center_y"] + side["outer_height"] / 2, f'OD {dimension_plan["outer_diameter"]}', 24)}
  {_svg_dim_v(side["x"] - 42, side["center_y"] - side["sections"][0]["diameter_px"] / 2, side["center_y"] + side["sections"][0]["diameter_px"] / 2, f'D1 {dimension_plan["shoulder_diameter"]}', -58)}
  {_svg_leader(side["x"] + side["sections"][0]["length_px"] + 12, side["center_y"] - side["sections"][0]["diameter_px"] / 2, side["x"] + side["sections"][0]["length_px"] + 92, side["y"] - 58, f'R {dimension_plan["radius_value"]}')}
  {_svg_leader(side["x"] + side["width"] - 10, side["center_y"] - side["sections"][-1]["diameter_px"] / 2 + 10, side["x"] + side["width"] + 84, side["y"] - 88, f'C {dimension_plan["chamfer_value"]} x 45deg')}
  <text x="{end["cx"] - 62}" y="{end["cy"] - end["outer_radius"] - 24}" class="view-label">Vista de extremo</text>
  <circle cx="{end["cx"]}" cy="{end["cy"]}" r="{end["outer_radius"]}" class="shape" />
  <circle cx="{end["cx"]}" cy="{end["cy"]}" r="{end["inner_radius"]}" class="shape" />
  <line x1="{end["cx"] - end["outer_radius"] - 24}" y1="{end["cy"]}" x2="{end["cx"] + end["outer_radius"] + 24}" y2="{end["cy"]}" class="center" />
  <line x1="{end["cx"]}" y1="{end["cy"] - end["outer_radius"] - 24}" x2="{end["cx"]}" y2="{end["cy"] + end["outer_radius"] + 24}" class="center" />
  <text x="{section["x"]}" y="{section["y"] - 16}" class="view-label">Corte longitudinal</text>
  {section_rects}
  {hatch_lines}
  <rect x="{section["x"]}" y="{section["center_y"] - section["bore_height"] / 2}" width="{section["width"]}" height="{section["bore_height"]}" fill="#fff" stroke="#0f172a" stroke-width="1.6" />
  <line x1="{section["x"] - 18}" y1="{section["center_y"]}" x2="{section["x"] + section["width"] + 18}" y2="{section["center_y"]}" class="center" />
  {_svg_dim_v(section["x"] + section["width"] + 46, section["center_y"] - section["bore_height"] / 2, section["center_y"] + section["bore_height"] / 2, f'ID {dimension_plan["bore_diameter"]}', 24)}
  <text x="{notes_box["x"] + 16}" y="{notes_box["y"] + 18}" class="view-label">Notas generales</text>
  {svg_notes}
  {svg_title}
</svg>"""


def draw_axial_sheet_pdf(pdf, sheet_data: dict[str, object], project_name: str) -> None:
    view_layout = sheet_data["view_layout"]
    dimension_plan = sheet_data["dimension_plan"]
    title = view_layout["title_block"]
    notes_box = view_layout["notes_box"]
    side = view_layout["side"]
    section = view_layout["section"]
    end = view_layout["end"]
    pdf.setTitle(f"Plano axial - {project_name}")
    pdf.setLineWidth(2)
    pdf.rect(view_layout["frame"]["margin"], view_layout["frame"]["margin"], sheet_data["sheet_width"] - view_layout["frame"]["margin"] * 2, sheet_data["sheet_height"] - view_layout["frame"]["margin"] * 2)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(58, sheet_data["sheet_height"] - 48, project_name)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(58, sheet_data["sheet_height"] - 64, "Hoja axial preliminar vectorial")
    for x, y, w, h in _rectangles_for(side["x"], side["center_y"], side["sections"]):
        pdf.rect(x, y, w, h)
    pdf.line(side["x"] - 18, side["center_y"], side["x"] + side["width"] + 18, side["center_y"])
    pdf.drawString(side["x"], side["y"] - 18, "Vista lateral principal")
    pdf.circle(end["cx"], end["cy"], end["outer_radius"])
    pdf.circle(end["cx"], end["cy"], end["inner_radius"])
    pdf.drawString(end["cx"] - 60, end["cy"] - end["outer_radius"] - 18, "Vista de extremo")
    for x, y, w, h in _rectangles_for(section["x"], section["center_y"], section["segments"]):
        pdf.rect(x, y, w, h)
        _pdf_hatch(pdf, x, y, w, h)
    pdf.rect(section["x"], section["center_y"] - section["bore_height"] / 2, section["width"], section["bore_height"], stroke=1, fill=0)
    pdf.drawString(section["x"], section["y"] - 18, "Corte longitudinal")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(side["x"], side["y"] + side["outer_height"] + 52, f"L total {dimension_plan['overall_length']} mm")
    pdf.drawString(side["x"] + side["width"] + 56, side["center_y"], f"OD {dimension_plan['outer_diameter']}")
    pdf.drawString(side["x"] - 86, side["center_y"], f"D1 {dimension_plan['shoulder_diameter']}")
    pdf.drawString(section["x"] + section["width"] + 48, section["center_y"], f"ID {dimension_plan['bore_diameter']}")
    pdf.drawString(side["x"] + 120, side["y"] - 36, f"R {dimension_plan['radius_value']}")
    pdf.drawString(side["x"] + side["width"] - 36, side["y"] - 56, f"C {dimension_plan['chamfer_value']} x 45deg")
    pdf.rect(notes_box["x"], notes_box["y"], notes_box["width"], notes_box["height"])
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(notes_box["x"] + 12, notes_box["y"] + notes_box["height"] - 18, "Notas generales")
    pdf.setFont("Helvetica", 9)
    for index, note in enumerate(sheet_data["notes"]):
        pdf.drawString(notes_box["x"] + 12, notes_box["y"] + notes_box["height"] - 34 - index * 14, note)
    pdf.rect(title["x"], title["y"], title["width"], title["height"])
    current_y = title["y"] + title["height"] - 18
    for index, (label, value) in enumerate(sheet_data["title_block"].items()):
        col_x = title["x"] + 14 if index % 2 == 0 else title["x"] + title["width"] / 2 + 8
        if index % 2 == 0 and index > 0:
            current_y -= 18
        pdf.drawString(col_x, current_y, f"{label}: {value}")


def draw_axial_sheet_dxf(msp, sheet_data: dict[str, object], project_name: str) -> None:
    view_layout = sheet_data["view_layout"]
    dimension_plan = sheet_data["dimension_plan"]
    side = view_layout["side"]
    section = view_layout["section"]
    end = view_layout["end"]
    _dxf_rect(msp, view_layout["frame"]["margin"], view_layout["frame"]["margin"], sheet_data["sheet_width"] - view_layout["frame"]["margin"] * 2, sheet_data["sheet_height"] - view_layout["frame"]["margin"] * 2)
    msp.add_text(project_name, dxfattribs={"height": 10}).set_placement((58, sheet_data["sheet_height"] - 48))
    for x, y, w, h in _rectangles_for(side["x"], side["center_y"], side["sections"]):
        _dxf_rect(msp, x, y, w, h)
    msp.add_text("Vista lateral principal", dxfattribs={"height": 4}).set_placement((side["x"], side["y"] - 18))
    msp.add_circle((end["cx"], end["cy"]), end["outer_radius"])
    msp.add_circle((end["cx"], end["cy"]), end["inner_radius"])
    msp.add_text("Vista de extremo", dxfattribs={"height": 4}).set_placement((end["cx"] - 60, end["cy"] - end["outer_radius"] - 18))
    for x, y, w, h in _rectangles_for(section["x"], section["center_y"], section["segments"]):
        _dxf_rect(msp, x, y, w, h)
        _dxf_hatch(msp, x, y, w, h)
    _dxf_rect(msp, section["x"], section["center_y"] - section["bore_height"] / 2, section["width"], section["bore_height"])
    msp.add_text("Corte longitudinal", dxfattribs={"height": 4}).set_placement((section["x"], section["y"] - 18))
    msp.add_text(f"L total {dimension_plan['overall_length']}", dxfattribs={"height": 4}).set_placement((side["x"], side["y"] + side["outer_height"] + 54))
    msp.add_text(f"OD {dimension_plan['outer_diameter']}", dxfattribs={"height": 4}).set_placement((side["x"] + side["width"] + 56, side["center_y"]))
    msp.add_text(f"D1 {dimension_plan['shoulder_diameter']}", dxfattribs={"height": 4}).set_placement((side["x"] - 86, side["center_y"]))
    msp.add_text(f"ID {dimension_plan['bore_diameter']}", dxfattribs={"height": 4}).set_placement((section["x"] + section["width"] + 48, section["center_y"]))
    msp.add_text(f"R {dimension_plan['radius_value']}", dxfattribs={"height": 4}).set_placement((side["x"] + 120, side["y"] - 36))
    msp.add_text(f"C {dimension_plan['chamfer_value']} x 45deg", dxfattribs={"height": 4}).set_placement((side["x"] + side["width"] - 36, side["y"] - 56))


def _get_or_create_strategy(*, project: Project, uploaded_model: UploadedModel, upload_root: Path, freecad_lib_path: str | None) -> DrawingJob:
    existing = DrawingJob.query.filter_by(project_id=project.id, uploaded_model_id=uploaded_model.id, output_type="axial_strategy", status="completed").order_by(DrawingJob.created_at.desc()).first()
    if existing is not None:
        return existing
    return generate_axial_drawing_strategy(project=project, uploaded_model=uploaded_model, upload_root=upload_root, freecad_lib_path=freecad_lib_path)


def _get_completed_analysis(*, project: Project, uploaded_model: UploadedModel) -> DrawingJob | None:
    return DrawingJob.query.filter_by(project_id=project.id, uploaded_model_id=uploaded_model.id, output_type="model_analysis", status="completed").order_by(DrawingJob.created_at.desc()).first()


def _resolve_template(project: Project) -> Template | None:
    return project.template or Template.query.filter_by(is_default=True).order_by(Template.id.asc()).first()


def _resolve_template_spec(template: Template | None) -> dict[str, object]:
    return SHEET_SPECS.get(template.code if template else "industrial-a4", SHEET_SPECS["industrial-a4"])


def _build_title_block(project: Project, scale_label: str) -> dict[str, str]:
    return {
        "Fecha": datetime.utcnow().strftime("%Y-%m-%d"),
        "Nombre": project.resolved_part_name,
        "Revision": project.revision or "A",
        "Dibujo": project.author or "Sin autor",
        "Aprobo": "Pendiente",
        "Material": project.material or "No definido",
        "Tratamiento": project.finish or "No definido",
        "Escala": scale_label,
        "Unidades": "mm",
        "Proyecto": project.resolved_project_name,
    }


def _build_view_layout(template_spec: dict[str, object], dimension_plan: dict[str, object], scale_factor: float) -> dict[str, object]:
    width = float(template_spec["width"])
    height = float(template_spec["height"])
    margin = 38.0
    title_height = 168.0
    segments = []
    current = 0.0
    for section in dimension_plan["sections"]:
        length_px = round(float(section["length"]) * scale_factor, 3)
        diameter_px = round(float(section["diameter"]) * scale_factor, 3)
        segments.append({"label": section["label"], "length": section["length"], "diameter": section["diameter"], "length_px": length_px, "diameter_px": diameter_px, "x_offset": round(current * scale_factor, 3)})
        current += float(section["length"])
    overall_width = round(float(dimension_plan["overall_length"]) * scale_factor, 3)
    outer_height = round(float(dimension_plan["outer_diameter"]) * scale_factor, 3)
    bore_height = round(float(dimension_plan["bore_diameter"]) * scale_factor, 3)
    return {
        "frame": {"margin": margin},
        "title_block": {"x": margin, "y": height - title_height - margin, "width": width - margin * 2, "height": title_height},
        "notes_box": {"x": width - 360.0, "y": 156.0, "width": 250.0, "height": 126.0},
        "side": {"x": 92.0, "y": 170.0, "center_y": 170.0 + outer_height / 2, "width": overall_width, "outer_height": outer_height, "sections": segments},
        "end": {"cx": width - 250.0, "cy": 288.0, "outer_radius": outer_height / 2, "inner_radius": bore_height / 2},
        "section": {"x": 92.0, "y": 452.0, "center_y": 452.0 + outer_height / 2, "width": overall_width, "outer_height": outer_height, "bore_height": bore_height, "segments": segments},
    }


def _build_scale_label(scale_factor: float) -> str:
    return f"{round(scale_factor, 2)}:1" if scale_factor >= 1 else f"1:{round(1 / scale_factor, 2)}"


def _svg_rectangles(start_x: float, center_y: float, sections: list[dict[str, object]]) -> list[str]:
    rects = []
    current_x = start_x
    for section in sections:
        rects.append(f'<rect x="{round(current_x, 3)}" y="{round(center_y - section["diameter_px"] / 2, 3)}" width="{section["length_px"]}" height="{section["diameter_px"]}" class="shape" />')
        current_x += section["length_px"]
    return rects


def _svg_hatch(x: float, y: float, width: float, height: float) -> list[str]:
    lines = []
    current = 0.0
    while current <= width + height:
        x1 = x + max(current - height, 0)
        y1 = y + min(current, height)
        x2 = x + min(current, width)
        y2 = y + max(current - width, 0)
        lines.append(f'<line x1="{round(x1, 3)}" y1="{round(y1, 3)}" x2="{round(x2, 3)}" y2="{round(y2, 3)}" class="hatch" />')
        current += 18.0
    return lines


def _svg_dim_h(x1: float, x2: float, y: float, label: str) -> str:
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="dim" /><text x="{(x1 + x2) / 2 - 24}" y="{y - 8}" class="dim-text">{escape(label)}</text>'


def _svg_dim_v(x: float, y1: float, y2: float, label: str, shift: float) -> str:
    return f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" class="dim" /><text x="{x + shift}" y="{(y1 + y2) / 2}" class="dim-text">{escape(label)}</text>'


def _svg_leader(x1: float, y1: float, x2: float, y2: float, label: str) -> str:
    return f'<line x1="{x2}" y1="{y2}" x2="{x1}" y2="{y1}" class="leader-single" /><text x="{x2 - 6}" y="{y2 - 6}" class="dim-text">{escape(label)}</text>'


def _rectangles_for(start_x: float, center_y: float, sections: list[dict[str, object]]) -> list[tuple[float, float, float, float]]:
    rects = []
    current_x = start_x
    for section in sections:
        rects.append((current_x, center_y - section["diameter_px"] / 2, section["length_px"], section["diameter_px"]))
        current_x += section["length_px"]
    return rects


def _pdf_hatch(pdf, x: float, y: float, width: float, height: float) -> None:
    current = 0.0
    while current <= width + height:
        x1 = x + max(current - height, 0)
        y1 = y + min(current, height)
        x2 = x + min(current, width)
        y2 = y + max(current - width, 0)
        pdf.line(x1, y1, x2, y2)
        current += 18.0


def _dxf_rect(msp, x: float, y: float, width: float, height: float) -> None:
    msp.add_line((x, y), (x + width, y))
    msp.add_line((x + width, y), (x + width, y + height))
    msp.add_line((x + width, y + height), (x, y + height))
    msp.add_line((x, y + height), (x, y))


def _dxf_hatch(msp, x: float, y: float, width: float, height: float) -> None:
    current = 0.0
    while current <= width + height:
        x1 = x + max(current - height, 0)
        y1 = y + min(current, height)
        x2 = x + min(current, width)
        y2 = y + max(current - width, 0)
        msp.add_line((x1, y1), (x2, y2))
        current += 18.0


def _create_failed_sheet_job(*, project: Project, uploaded_model: UploadedModel, message: str) -> DrawingJob:
    sheet_job = DrawingJob(
        project_id=project.id,
        template_id=project.template_id,
        uploaded_model_id=uploaded_model.id,
        status="failed",
        output_type="axial_sheet",
        analyzer_backend="axial_template_service",
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        error_message=message,
    )
    db.session.add(sheet_job)
    db.session.commit()
    return sheet_job
