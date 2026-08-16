from functools import wraps

from flask import Blueprint, abort, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.item import Item

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def campus_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user.email.lower() not in current_app.config['CAMPUS_ADMIN_EMAILS']:
            abort(403)
        return view(*args, **kwargs)
    return login_required(wrapped)


@admin_bp.route('/')
@campus_admin_required
def moderation():
    items = Item.query.order_by(Item.created_at.desc()).limit(100).all()
    return render_template('admin_moderation.html', items=items)


@admin_bp.route('/item/<int:item_id>/resolve', methods=['POST'])
@campus_admin_required
def resolve(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)
    item.status = 'resolved'
    db.session.commit()
    flash(f'Admin moderation: {item.title} marked resolved.', 'success')
    return redirect(url_for('admin.moderation'))
