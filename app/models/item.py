from datetime import datetime
from app.extensions import db

class Item(db.Model):
    """Database model for lost and found item reports."""
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'lost' or 'found'
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    color = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(150), nullable=False)
    date = db.Column(db.Date, nullable=False)  # SQLAlchemy Date field for reliable date comparison
    image_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active' or 'resolved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Item id={self.id} type='{self.item_type}' title='{self.title}' status='{self.status}'>"
