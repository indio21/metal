from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Project, UploadedModel


ALLOWED_MODEL_EXTENSIONS = {".step", ".stp", ".iges", ".igs"}


class UploadValidationError(Exception):
    pass


class UploadStorageError(Exception):
    pass


def handle_model_upload(
    *,
    project: Project,
    file_storage: FileStorage | None,
    upload_root: Path,
) -> UploadedModel:
    if file_storage is None:
        raise UploadValidationError("Debes seleccionar un archivo STEP o IGES.")

    original_filename = (file_storage.filename or "").strip()
    if not original_filename:
        raise UploadValidationError("Debes seleccionar un archivo STEP o IGES.")

    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_MODEL_EXTENSIONS:
        raise UploadValidationError(
            "Formato no soportado. Solo se aceptan archivos .step, .stp, .iges o .igs."
        )

    safe_original_name = secure_filename(original_filename)
    if not safe_original_name:
        raise UploadValidationError("El nombre del archivo no es valido.")

    project_folder = upload_root / f"project_{project.id}"
    project_folder.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{project.id}_{uuid4().hex}{extension}"
    destination = project_folder / stored_filename

    try:
        file_storage.save(destination)
    except OSError as error:
        raise UploadStorageError("No se pudo guardar el archivo en uploads.") from error

    uploaded_model = UploadedModel(
        project_id=project.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_format=extension.lstrip("."),
        storage_path=str(destination.relative_to(upload_root)),
        status="uploaded",
    )
    db.session.add(uploaded_model)
    db.session.commit()
    return uploaded_model


def resolve_uploaded_model_path(upload_root: Path, uploaded_model: UploadedModel) -> Path:
    if not uploaded_model.storage_path:
        raise UploadStorageError("El archivo no tiene una ruta almacenada.")

    candidate = (upload_root / uploaded_model.storage_path).resolve()
    try:
        candidate.relative_to(upload_root.resolve())
    except ValueError as error:
        raise UploadStorageError("La ruta del archivo almacenado es invalida.") from error

    if not candidate.exists():
        raise UploadStorageError("El archivo asociado no existe en disco.")

    return candidate
