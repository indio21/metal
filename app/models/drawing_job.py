import json

from app.extensions import db
from app.models.mixins import TimestampMixin


class DrawingJob(TimestampMixin, db.Model):
    __tablename__ = "drawing_jobs"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=True, index=True)
    uploaded_model_id = db.Column(
        db.Integer,
        db.ForeignKey("uploaded_models.id"),
        nullable=True,
        index=True,
    )
    status = db.Column(db.String(32), nullable=False, default="pending")
    output_type = db.Column(db.String(32), nullable=False, default="preliminary_2d")
    analyzer_backend = db.Column(db.String(64), nullable=True)
    analysis_summary = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    project = db.relationship("Project", back_populates="drawing_jobs")
    template = db.relationship("Template", back_populates="drawing_jobs")
    uploaded_model = db.relationship("UploadedModel", back_populates="drawing_jobs")
    export_files = db.relationship(
        "ExportFile",
        back_populates="drawing_job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def analysis_data(self) -> dict[str, object]:
        if not self.analysis_summary:
            return {}
        try:
            return json.loads(self.analysis_summary)
        except json.JSONDecodeError:
            return {}

    def __repr__(self) -> str:
        return f"<DrawingJob {self.project_id}:{self.status}>"
