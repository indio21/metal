from app.extensions import db
from app.models.mixins import TimestampMixin


class UploadedModel(TimestampMixin, db.Model):
    __tablename__ = "uploaded_models"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=True)
    stored_filename = db.Column(db.String(255), nullable=True)
    file_format = db.Column(db.String(16), nullable=True)
    storage_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="pending_upload")

    project = db.relationship("Project", back_populates="uploaded_models")

    def __repr__(self) -> str:
        return f"<UploadedModel {self.original_filename or 'pending'}>"
