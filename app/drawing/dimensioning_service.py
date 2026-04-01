from __future__ import annotations

from dataclasses import dataclass

from app.models import Project


@dataclass
class AxialSection:
    label: str
    length: float
    diameter: float

    def as_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "length": round(self.length, 3),
            "diameter": round(self.diameter, 3),
        }


@dataclass
class DimensionCallout:
    kind: str
    label: str
    value: float | str
    placement: str

    def as_dict(self) -> dict[str, object]:
        value = round(self.value, 3) if isinstance(self.value, (int, float)) else self.value
        return {
            "kind": self.kind,
            "label": self.label,
            "value": value,
            "placement": self.placement,
        }


class DimensioningError(Exception):
    pass


def build_axial_dimensioning(
    *,
    project: Project,
    analysis_data: dict[str, object],
    default_tolerance_note: str,
    default_edge_note: str,
) -> dict[str, object]:
    dimensions = analysis_data.get("dimensions", {})
    dominant_axis = str(analysis_data.get("dominant_axis") or "x")
    long_dim, outer_diameter, inner_reference = _resolve_orientation(dimensions, dominant_axis)
    if long_dim <= 0 or outer_diameter <= 0:
        raise DimensioningError("No hay dimensiones validas para construir el acotado axial.")

    finish_factor = 0.82 if project.finish else 0.78
    shoulder_diameter = max(round(outer_diameter * finish_factor, 3), round(outer_diameter * 0.58, 3))
    bore_diameter = max(round(inner_reference * 0.52, 3), round(outer_diameter * 0.24, 3))
    bore_diameter = min(bore_diameter, round(shoulder_diameter * 0.7, 3))

    first_length = round(max(long_dim * 0.18, 8.0), 3)
    second_length = round(max(long_dim * 0.37, 12.0), 3)
    third_length = round(max(long_dim - first_length - second_length, long_dim * 0.20), 3)
    length_balance = round(long_dim - (first_length + second_length + third_length), 3)
    third_length = round(third_length + length_balance, 3)

    radius_value = round(max(outer_diameter * 0.05, 0.8), 3)
    chamfer_value = round(max(min(outer_diameter * 0.035, 2.0), 0.5), 3)

    sections = [
        AxialSection(label="L1", length=first_length, diameter=shoulder_diameter),
        AxialSection(label="L2", length=second_length, diameter=outer_diameter),
        AxialSection(label="L3", length=third_length, diameter=round(max(outer_diameter * 0.9, shoulder_diameter), 3)),
    ]

    axial_dimensions = [
        DimensionCallout(kind="axial", label="L total", value=long_dim, placement="bottom_overall"),
        DimensionCallout(kind="axial", label="L1", value=first_length, placement="top_segment_1"),
        DimensionCallout(kind="axial", label="L2", value=second_length, placement="top_segment_2"),
        DimensionCallout(kind="axial", label="L3", value=third_length, placement="top_segment_3"),
    ]
    diameter_dimensions = [
        DimensionCallout(kind="diameter", label="OD", value=outer_diameter, placement="right_overall"),
        DimensionCallout(kind="diameter", label="D1", value=shoulder_diameter, placement="left_step"),
        DimensionCallout(kind="diameter", label="ID", value=bore_diameter, placement="section_inner"),
    ]
    leader_callouts = [
        DimensionCallout(kind="radius", label="R", value=radius_value, placement="lateral_transition"),
        DimensionCallout(kind="chamfer", label="C", value=f"{chamfer_value} x 45deg", placement="front_chamfer"),
    ]

    notes = [
        default_tolerance_note,
        default_edge_note,
        "Plano preliminar editable. Verificar cotas criticas antes de liberar a taller.",
    ]

    return {
        "dominant_axis": dominant_axis,
        "sections": [section.as_dict() for section in sections],
        "axial_dimensions": [dimension.as_dict() for dimension in axial_dimensions],
        "diameter_dimensions": [dimension.as_dict() for dimension in diameter_dimensions],
        "leader_callouts": [dimension.as_dict() for dimension in leader_callouts],
        "general_notes": notes,
        "centerline": True,
        "overall_length": round(long_dim, 3),
        "outer_diameter": round(outer_diameter, 3),
        "shoulder_diameter": round(shoulder_diameter, 3),
        "bore_diameter": round(bore_diameter, 3),
        "radius_value": round(radius_value, 3),
        "chamfer_value": round(chamfer_value, 3),
        "units": "mm",
    }


def _resolve_orientation(dimensions: dict[str, object], dominant_axis: str) -> tuple[float, float, float]:
    axis_map = {axis: float(dimensions.get(axis, 0.0) or 0.0) for axis in ("x", "y", "z")}
    long_dim = axis_map.get(dominant_axis, 0.0)
    radial_axes = [axis for axis in ("x", "y", "z") if axis != dominant_axis]
    radial_values = [axis_map[axis] for axis in radial_axes]
    outer_diameter = max(radial_values) if radial_values else 0.0
    inner_reference = min(radial_values) if radial_values else outer_diameter
    return long_dim, outer_diameter, inner_reference
