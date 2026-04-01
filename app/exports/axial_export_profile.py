"""Base stubs for export profiles in version 2.0."""

from dataclasses import dataclass


@dataclass
class AxialExportProfile:
    preview_format: str = "svg"
    final_formats: tuple[str, ...] = ("pdf", "dxf")
    notes: str = (
        "Stub inicial del perfil de exportacion axial. "
        "En fases siguientes se conectara con drawing especializado "
        "y salida vectorial similar al ejemplo del cliente."
    )


def build_axial_export_profile() -> AxialExportProfile:
    return AxialExportProfile()
