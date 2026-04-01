"""Base stubs for axial drawing strategy in version 2.0."""

from dataclasses import dataclass


@dataclass
class AxialDrawingPlan:
    family: str = "axial"
    primary_view: str = "lateral"
    secondary_view: str = "extremo"
    tertiary_view: str = "corte_longitudinal"
    notes: str = (
        "Stub inicial de la estrategia 2.0. "
        "En fases siguientes se completara con deteccion axial, "
        "layout especializado y cotas propias de piezas torneadas."
    )


def build_axial_drawing_plan() -> AxialDrawingPlan:
    return AxialDrawingPlan()
