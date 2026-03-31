from app.extensions import db
from app.models.mixins import TimestampMixin


class ExportFile(TimestampMixin, db.Model):
    __tablename__ = "export_files"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    drawing_job_id = db.Column(db.Integer, db.ForeignKey("drawing_jobs.id"), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=True)
    file_format = db.Column(db.String(16), nullable=False, default="pdf")
    file_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="pending")

    project = db.relationship("Project", back_populates="export_files")
    drawing_job = db.relationship("DrawingJob", back_populates="export_files")

    def __repr__(self) -> str:
        return f"<ExportFile {self.file_format}:{self.status}>"
