from app.extensions import db
from app.models.mixins import TimestampMixin


class Template(TimestampMixin, db.Model):
    __tablename__ = "templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    projects = db.relationship("Project", back_populates="template", lazy="selectin")
    drawing_jobs = db.relationship("DrawingJob", back_populates="template", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Template {self.code}>"
