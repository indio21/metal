from datetime import datetime

from app.extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    part_number = db.Column(db.String(80), nullable=True)
    material = db.Column(db.String(80), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="draft")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Project {self.name}>"
