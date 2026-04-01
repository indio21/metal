from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.drawing.template_service import draw_axial_sheet_dxf, draw_axial_sheet_pdf
from app.extensions import db
from app.models import DrawingJob, ExportFile, Project


class ExportDependencyError(Exception):
    pass


class ExportGenerationError(Exception):
    pass


@dataclass
class ExportResult:
    file_format: str
    filename: str
    relative_path: str
    backend: str


def generate_export_file(
    *,
    project: Project,
    drawing_job: DrawingJob,
    export_root: Path,
    target_format: str,
) -> ExportFile:
    if drawing_job.status != "completed":
        raise ExportGenerationError("El drawing debe estar completado antes de exportar.")

    target_format = target_format.lower()
    if target_format not in {"pdf", "dxf"}:
        raise ExportGenerationError("Formato de exportacion no soportado.")

    export_dir = export_root / f"project_{project.id}"
    export_dir.mkdir(parents=True, exist_ok=True)

    filename = f"drawing_{project.id}_{drawing_job.id}_{uuid4().hex[:8]}.{target_format}"
    export_path = export_dir / filename

    if target_format == "pdf":
        backend = _export_pdf(drawing_job=drawing_job, project=project, export_path=export_path)
    else:
        backend = _export_dxf(drawing_job=drawing_job, project=project, export_path=export_path)

    export_file = ExportFile(
        project_id=project.id,
        drawing_job_id=drawing_job.id,
        filename=filename,
        file_format=target_format,
        file_path=str(export_path.relative_to(export_root)),
        status="generated",
    )
    db.session.add(export_file)
    db.session.commit()
    return export_file


def resolve_generated_export_path(export_root: Path, export_file: ExportFile) -> Path:
    if not export_file.file_path:
        raise ExportGenerationError("El archivo exportado no tiene una ruta almacenada.")

    candidate = (export_root / export_file.file_path).resolve()
    try:
        candidate.relative_to(export_root.resolve())
    except ValueError as error:
        raise ExportGenerationError("La ruta del archivo exportado es invalida.") from error

    if not candidate.exists():
        raise ExportGenerationError("El archivo exportado no existe en disco.")

    return candidate


def _export_pdf(*, drawing_job: DrawingJob, project: Project, export_path: Path) -> str:
    drawing = drawing_job.analysis_data
    if drawing_job.output_type == "axial_sheet" and drawing.get("sheet_type") == "axial_turned_sheet":
        try:
            from reportlab.pdfgen import canvas
        except ImportError as error:
            raise ExportDependencyError(
                "La exportacion a PDF requiere reportlab. Ejecuta 'pip install reportlab'."
            ) from error

        pdf = canvas.Canvas(str(export_path), pagesize=(drawing["sheet_width"], drawing["sheet_height"]))
        draw_axial_sheet_pdf(pdf, drawing, project.resolved_part_name)
        pdf.showPage()
        pdf.save()
        return "reportlab_axial_sheet"

    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas
    except ImportError as error:
        raise ExportDependencyError(
            "La exportacion a PDF requiere reportlab. Ejecuta 'pip install reportlab'."
        ) from error

    drawing = drawing_job.analysis_data
    dimensions = drawing.get("dimensions", {})
    title_block = drawing.get("title_block", {})

    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(str(export_path), pagesize=(page_width, page_height))
    pdf.setTitle(f"Drawing preliminar - {project.name}")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(36, page_height - 36, f"Drawing preliminar - {project.name}")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(36, page_height - 54, f"Escala: {drawing.get('scale_label', 'Sin escala')}")
    pdf.drawString(36, page_height - 68, f"Backend: {drawing_job.analyzer_backend or 'svg_fallback'}")

    _draw_pdf_views(pdf, dimensions, page_width, page_height)

    title_y = 120
    pdf.rect(24, 24, page_width - 48, title_y, stroke=1, fill=0)
    pdf.setFont("Helvetica-Bold", 9)
    fields = list(title_block.items())
    for index, (label, value) in enumerate(fields):
        x = 36 if index % 2 == 0 else page_width / 2
        y = 110 - (index // 2) * 16
        pdf.drawString(x, y, f"{label}:")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(x + 64, y, str(value))
        pdf.setFont("Helvetica-Bold", 9)

    pdf.showPage()
    pdf.save()
    return "reportlab"


def _draw_pdf_views(pdf, dimensions: dict[str, float], page_width: float, page_height: float) -> None:
    dim_x = float(dimensions.get("x", 100.0) or 100.0)
    dim_y = float(dimensions.get("y", 50.0) or 50.0)
    dim_z = float(dimensions.get("z", 30.0) or 30.0)
    max_dim = max(dim_x, dim_y, dim_z, 1.0)
    scale = min(240 / max(dim_x, dim_y), 140 / max(dim_z, 1.0), 2.0)

    front_x = 70
    front_y = page_height - 300
    front_w = dim_x * scale
    front_h = dim_z * scale
    top_x = 70
    top_y = page_height - 150
    top_w = dim_x * scale
    top_h = dim_y * scale
    side_x = 360
    side_y = page_height - 300
    side_w = dim_y * scale
    side_h = dim_z * scale

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(top_x, top_y + top_h + 18, "Vista superior")
    pdf.drawString(front_x, front_y + front_h + 18, "Vista frontal")
    pdf.drawString(side_x, side_y + side_h + 18, "Vista lateral")
    pdf.drawString(540, page_height - 128, "Vista isometrica")

    pdf.rect(top_x, top_y, top_w, top_h)
    pdf.rect(front_x, front_y, front_w, front_h)
    pdf.rect(side_x, side_y, side_w, side_h)

    iso_x = 560
    iso_y = page_height - 220
    iso_w = dim_x * scale * 0.55
    iso_h = dim_z * scale * 0.55
    iso_d = dim_y * scale * 0.28
    pdf.line(iso_x, iso_y, iso_x + iso_w, iso_y + iso_d)
    pdf.line(iso_x + iso_w, iso_y + iso_d, iso_x + iso_w, iso_y + iso_d + iso_h)
    pdf.line(iso_x, iso_y, iso_x, iso_y + iso_h)
    pdf.line(iso_x, iso_y + iso_h, iso_x + iso_w, iso_y + iso_h + iso_d)
    pdf.line(iso_x + iso_w, iso_y + iso_d + iso_h, iso_x + iso_w, iso_y + iso_d)
    pdf.line(iso_x, iso_y + iso_h, iso_x + iso_w, iso_y + iso_h + iso_d)

    pdf.setFont("Helvetica", 9)
    pdf.drawString(front_x + front_w / 2 - 18, front_y - 14, f"X {round(dim_x, 2)}")
    pdf.drawString(front_x - 38, front_y + front_h / 2, f"Z {round(dim_z, 2)}")
    pdf.drawString(side_x + side_w / 2 - 18, side_y - 14, f"Y {round(dim_y, 2)}")


def _export_dxf(*, drawing_job: DrawingJob, project: Project, export_path: Path) -> str:
    drawing = drawing_job.analysis_data
    if drawing_job.output_type == "axial_sheet" and drawing.get("sheet_type") == "axial_turned_sheet":
        try:
            import ezdxf
        except ImportError as error:
            raise ExportDependencyError(
                "La exportacion a DXF requiere ezdxf. Ejecuta 'pip install ezdxf'."
            ) from error

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        draw_axial_sheet_dxf(msp, drawing, project.resolved_part_name)
        doc.saveas(export_path)
        return "ezdxf_axial_sheet"

    try:
        import ezdxf
    except ImportError as error:
        raise ExportDependencyError(
            "La exportacion a DXF requiere ezdxf. Ejecuta 'pip install ezdxf'."
        ) from error

    dimensions = drawing.get("dimensions", {})
    dim_x = float(dimensions.get("x", 100.0) or 100.0)
    dim_y = float(dimensions.get("y", 50.0) or 50.0)
    dim_z = float(dimensions.get("z", 30.0) or 30.0)

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_text(f"Drawing preliminar - {project.name}", dxfattribs={"height": 8}).set_placement((0, 210))
    msp.add_text(f"Escala {drawing.get('scale_label', 'Sin escala')}", dxfattribs={"height": 4}).set_placement((0, 198))

    _add_rect(msp, x=0, y=120, width=dim_x, height=dim_z)
    _add_rect(msp, x=0, y=20, width=dim_x, height=dim_y)
    _add_rect(msp, x=180, y=120, width=dim_y, height=dim_z)

    msp.add_text("Vista frontal", dxfattribs={"height": 4}).set_placement((0, 160))
    msp.add_text("Vista superior", dxfattribs={"height": 4}).set_placement((0, 70))
    msp.add_text("Vista lateral", dxfattribs={"height": 4}).set_placement((180, 160))

    msp.add_text(f"REV {project.revision}", dxfattribs={"height": 4}).set_placement((260, 20))
    msp.add_text(f"MAT {project.material or 'N/D'}", dxfattribs={"height": 4}).set_placement((260, 12))
    msp.add_text(f"AUTOR {project.author or 'N/D'}", dxfattribs={"height": 4}).set_placement((260, 4))

    doc.saveas(export_path)
    return "ezdxf"


def _add_rect(msp, *, x: float, y: float, width: float, height: float) -> None:
    msp.add_line((x, y), (x + width, y))
    msp.add_line((x + width, y), (x + width, y + height))
    msp.add_line((x + width, y + height), (x, y + height))
    msp.add_line((x, y + height), (x, y))
