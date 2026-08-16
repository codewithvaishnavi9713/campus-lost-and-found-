from datetime import datetime

from app.extensions import db


class Message(db.Model):
    """Private in-app communication about a reported item.

    Contact information intentionally is not stored in this model or rendered
    by messaging templates.  The two hide flags allow either participant to
    remove a message from their own view without deleting it for the other.
    """
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    subject = db.Column(db.String(150), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    deleted_by_sender = db.Column(db.Boolean, default=False, nullable=False)
    deleted_by_receiver = db.Column(db.Boolean, default=False, nullable=False)

    sender = db.relationship("User", foreign_keys=[sender_id], backref=db.backref("sent_messages", lazy=True))
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref=db.backref("received_messages", lazy=True))
    item = db.relationship("Item", backref=db.backref("messages", lazy=True))
