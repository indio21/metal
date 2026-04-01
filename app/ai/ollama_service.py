from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from app.models import DrawingJob, ExportFile, Project


class OllamaRequestError(Exception):
    pass


ACTION_META = {
    "technical_name": "Sugerir nombre tecnico",
    "description": "Sugerir descripcion",
    "missing_fields": "Advertir campos faltantes",
    "title_block": "Completar cajetin",
    "explain_output": "Explicar resultado",
}


@dataclass
class AssistanceResult:
    action: str
    title: str
    content: str
    backend: str
    used_fallback: bool
    notice: str | None = None


def get_ollama_runtime_status(config: dict[str, object]) -> dict[str, object]:
    return {
        "enabled": bool(config.get("OLLAMA_ENABLED", False)),
        "base_url": str(config.get("OLLAMA_BASE_URL") or "http://localhost:11434"),
        "model": str(config.get("OLLAMA_MODEL") or "llama3.2"),
    }


def request_project_assistance(
    *,
    project: Project,
    action: str,
    config: dict[str, object],
    latest_drawing_job: DrawingJob | None = None,
    export_history: list[ExportFile] | None = None,
) -> AssistanceResult:
    action = action if action in ACTION_META else "missing_fields"
    fallback_content = _build_local_assistance(
        project=project,
        action=action,
        latest_drawing_job=latest_drawing_job,
        export_history=export_history or [],
    )
    status = get_ollama_runtime_status(config)

    if not status["enabled"]:
        return AssistanceResult(
            action=action,
            title=ACTION_META[action],
            content=fallback_content,
            backend="local_fallback",
            used_fallback=True,
            notice="Ollama esta desactivado. Se muestra una ayuda local para no cortar el flujo.",
        )

    prompt = _build_prompt(
        project=project,
        action=action,
        latest_drawing_job=latest_drawing_job,
        export_history=export_history or [],
    )

    try:
        response_text = _call_ollama_generate(
            base_url=str(status["base_url"]),
            model=str(status["model"]),
            prompt=prompt,
        )
    except OllamaRequestError as error:
        return AssistanceResult(
            action=action,
            title=ACTION_META[action],
            content=fallback_content,
            backend="local_fallback",
            used_fallback=True,
            notice=f"No se pudo usar Ollama: {error}",
        )

    return AssistanceResult(
        action=action,
        title=ACTION_META[action],
        content=response_text.strip() or fallback_content,
        backend=f"ollama:{status['model']}",
        used_fallback=False,
        notice="Respuesta generada con asistencia opcional de Ollama.",
    )


def _call_ollama_generate(*, base_url: str, model: str, prompt: str) -> str:
    endpoint = f"{base_url.rstrip('/')}/api/generate"
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    http_request = request.Request(endpoint, data=payload, headers=headers, method="POST")

    try:
        with request.urlopen(http_request, timeout=20) as response:
            raw_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raise OllamaRequestError(f"HTTP {exc.code} al consultar {endpoint}.") from exc
    except error.URLError as exc:
        raise OllamaRequestError("Ollama no responde en la URL configurada.") from exc
    except TimeoutError as exc:
        raise OllamaRequestError("La consulta a Ollama excedio el tiempo de espera.") from exc

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise OllamaRequestError("La respuesta de Ollama no se pudo interpretar.") from exc

    content = str(data.get("response") or "").strip()
    if not content:
        raise OllamaRequestError("Ollama devolvio una respuesta vacia.")

    return content


def _build_prompt(
    *,
    project: Project,
    action: str,
    latest_drawing_job: DrawingJob | None,
    export_history: list[ExportFile],
) -> str:
    context = _build_project_context(project=project, latest_drawing_job=latest_drawing_job, export_history=export_history)
    instructions = {
        "technical_name": "Sugiere un nombre tecnico corto y serio para la pieza. Responde en espanol y en maximo 30 palabras.",
        "description": "Redacta una descripcion tecnica breve para la pieza. Responde en espanol y en maximo 70 palabras.",
        "missing_fields": "Indica los campos o datos faltantes mas importantes para completar la gestion de la pieza. Responde en espanol y en maximo 70 palabras.",
        "title_block": "Propone como completar el cajetin del plano con foco en pieza, revision, autor, material, escala y observaciones. Responde en espanol y en maximo 90 palabras.",
        "explain_output": "Explica de forma simple que genero la app hasta ahora para esta pieza y que falta. Responde en espanol y en maximo 90 palabras.",
    }
    return (
        "Actua como asistente tecnico para una app MVP de planos metalurgicos.\n"
        "No inventes capacidades que no esten presentes.\n"
        f"{instructions[action]}\n\n"
        f"Contexto de la pieza:\n{context}"
    )


def _build_project_context(
    *,
    project: Project,
    latest_drawing_job: DrawingJob | None,
    export_history: list[ExportFile],
) -> str:
    drawing_summary = latest_drawing_job.analysis_data if latest_drawing_job else {}
    return "\n".join(
        [
            f"Nombre: {project.name or 'No definido'}",
            f"Codigo: {project.part_number or 'No definido'}",
            f"Revision: {project.revision or 'No definida'}",
            f"Material: {project.material or 'No definido'}",
            f"Autor: {project.author or 'No definido'}",
            f"Template: {project.template.name if project.template else 'No definido'}",
            f"Observaciones: {project.notes or 'Sin observaciones'}",
            f"Estado: {project.status}",
            f"Modelos cargados: {len(project.uploaded_models)}",
            f"Drawing generado: {'si' if latest_drawing_job and latest_drawing_job.status == 'completed' else 'no'}",
            f"Escala drawing: {drawing_summary.get('scale_label', 'No definida')}",
            f"Exportaciones generadas: {len(export_history)}",
        ]
    )


def _build_local_assistance(
    *,
    project: Project,
    action: str,
    latest_drawing_job: DrawingJob | None,
    export_history: list[ExportFile],
) -> str:
    if action == "technical_name":
        return _suggest_local_name(project)
    if action == "description":
        return _suggest_local_description(project)
    if action == "title_block":
        return _suggest_local_title_block(project, latest_drawing_job)
    if action == "explain_output":
        return _explain_local_output(project, latest_drawing_job, export_history)
    return _warn_local_missing_fields(project, latest_drawing_job, export_history)


def _suggest_local_name(project: Project) -> str:
    material = project.material or "material pendiente"
    part_number = f" {project.part_number}" if project.part_number else ""
    return (
        f"Sugerencia base: {project.name}{part_number} - rev {project.revision}. "
        f"Si queres un nombre mas tecnico, agrega funcion de la pieza, proceso y material ({material})."
    )


def _suggest_local_description(project: Project) -> str:
    material = project.material or "material no definido"
    author = project.author or "autor no definido"
    notes = project.notes or "sin observaciones adicionales"
    return (
        f"Pieza individual para flujo preliminar de drawing metalurgico. "
        f"Revision {project.revision}, material {material}, responsable {author}. "
        f"Observaciones actuales: {notes}."
    )


def _warn_local_missing_fields(
    project: Project,
    latest_drawing_job: DrawingJob | None,
    export_history: list[ExportFile],
) -> str:
    missing_items: list[str] = []
    if not project.part_number:
        missing_items.append("codigo de pieza")
    if not project.material:
        missing_items.append("material")
    if not project.author:
        missing_items.append("autor")
    if not project.template:
        missing_items.append("template de plano")
    if not project.notes:
        missing_items.append("observaciones")
    if not project.uploaded_models:
        missing_items.append("archivo STEP/IGES")
    if latest_drawing_job is None or latest_drawing_job.status != "completed":
        missing_items.append("drawing preliminar generado")
    if not export_history:
        missing_items.append("exportacion PDF/DXF")

    if not missing_items:
        return "No se detectan campos criticos faltantes para este MVP. La pieza ya tiene un flujo base bastante completo."

    return "Faltantes sugeridos para revisar: " + ", ".join(missing_items) + "."


def _suggest_local_title_block(project: Project, latest_drawing_job: DrawingJob | None) -> str:
    drawing_data = latest_drawing_job.analysis_data if latest_drawing_job else {}
    scale_label = drawing_data.get("scale_label", "pendiente")
    return (
        f"Cajetin sugerido -> Pieza: {project.name}; Revision: {project.revision}; "
        f"Autor: {project.author or 'pendiente'}; Material: {project.material or 'pendiente'}; "
        f"Escala: {scale_label}; Observaciones: {project.notes or 'sin observaciones'}."
    )


def _explain_local_output(
    project: Project,
    latest_drawing_job: DrawingJob | None,
    export_history: list[ExportFile],
) -> str:
    if latest_drawing_job and latest_drawing_job.status == "completed":
        formats = ", ".join(sorted({export.file_format.upper() for export in export_history})) or "sin exportaciones finales"
        return (
            f"La app ya genero un drawing preliminar para {project.name}, con preview web SVG y soporte de exportacion en {formats}. "
            "El resultado sigue siendo una base de trabajo, no un plano universalmente acotado."
        )

    return (
        f"La app todavia no genero un drawing completo para {project.name}. "
        "El flujo actual permite gestionar la pieza, subir CAD y preparar el analisis previo."
    )
