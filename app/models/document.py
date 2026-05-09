from datetime import datetime
from ..extensions import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    document_type = db.Column(db.String(100), nullable=False)

    # ✅ Nom du fichier
    file_name = db.Column(db.String(255), nullable=False)

    # ✅ Type MIME
    mime_type = db.Column(db.String(100), nullable=True)

    # ✅ Contenu du fichier
    file_data = db.Column(db.LargeBinary, nullable=False)

    label = db.Column(db.String(150), nullable=True)

    status = db.Column(
        db.Enum("PENDING", "APPROVED", "REJECTED"),
        default="PENDING",
        nullable=False
    )

    comment = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="documents")