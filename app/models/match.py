from datetime import datetime

from app.extensions import db


class Match(db.Model):
    """A stored, explainable result of matching two opposite item reports."""
    __tablename__ = "matches"
    __table_args__ = (db.UniqueConstraint("source_item_id", "matched_item_id", name="uq_match_pair"),)

    id = db.Column(db.Integer, primary_key=True)
    source_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    matched_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    category_score = db.Column(db.Float, nullable=False)
    color_score = db.Column(db.Float, nullable=False)
    location_score = db.Column(db.Float, nullable=False)
    date_score = db.Column(db.Float, nullable=False)
    text_score = db.Column(db.Float, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    source_item = db.relationship("Item", foreign_keys=[source_item_id])
    matched_item = db.relationship("Item", foreign_keys=[matched_item_id])
