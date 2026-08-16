import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app.extensions import db
from app.models.item import Item
from app.ai.matcher import find_matches

items_bp = Blueprint('items', __name__)

ALLOWED_CATEGORIES = [
    'Electronics',
    'ID Cards & Keys',
    'Books & Stationery',
    'Clothing & Accessories',
    'Bags & Wallets',
    'Other'
]

def allowed_file(filename):
    """Checks if the filename extension is in the allowed list."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']

def is_valid_image_content(file_bytes):
    """Validates image content using magic byte signatures."""
    if not file_bytes or len(file_bytes) < 8:
        return False
    # PNG: \x89PNG\r\n\x1a\n
    if file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        return True
    # JPEG: \xff\xd8\xff
    if file_bytes.startswith(b'\xff\xd8\xff'):
        return True
    # GIF: GIF87a or GIF89a
    if file_bytes.startswith(b'GIF87a') or file_bytes.startswith(b'GIF89a'):
        return True
    # WEBP: RIFF...WEBP
    if file_bytes.startswith(b'RIFF') and b'WEBP' in file_bytes[:16]:
        return True
    return False

def handle_image_upload(file):
    """Securely validates and saves an uploaded image file."""
    if not file or not file.filename:
        return None, None

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return None, 'Invalid file type. Allowed formats: PNG, JPG, JPEG, WEBP, GIF.'

    # Read file content bytes for header verification
    file_bytes = file.read()
    file.seek(0)  # Reset pointer

    if not is_valid_image_content(file_bytes):
        return None, 'File content header validation failed. Please upload a genuine image file.'

    # Ensure upload directory exists
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    # Generate unique filename to prevent overwrite
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(upload_folder, unique_filename)
    file.save(save_path)
    
    return unique_filename, None


@items_bp.route('/report/lost', methods=['GET', 'POST'])
@login_required
def report_lost():
    """Report a lost item."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        color = request.form.get('color', '').strip()
        location = request.form.get('location', '').strip()
        date_str = request.form.get('date', '').strip()
        image_file = request.files.get('image')

        # Form Validation
        if not title or not category or not description or not location or not date_str:
            flash('Title, Category, Description, Location, and Date are required.', 'danger')
            return render_template('report_item.html', item_type='lost', categories=ALLOWED_CATEGORIES, form_data=request.form)

        if category not in ALLOWED_CATEGORIES:
            flash('Invalid category selected.', 'danger')
            return render_template('report_item.html', item_type='lost', categories=ALLOWED_CATEGORIES, form_data=request.form)

        try:
            item_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('report_item.html', item_type='lost', categories=ALLOWED_CATEGORIES, form_data=request.form)

        # Handle Optional Image Upload
        image_filename = None
        if image_file and image_file.filename:
            image_filename, err = handle_image_upload(image_file)
            if err:
                flash(err, 'danger')
                return render_template('report_item.html', item_type='lost', categories=ALLOWED_CATEGORIES, form_data=request.form)

        # Create Item Record
        item = Item(
            user_id=current_user.id,
            item_type='lost',
            title=title,
            category=category,
            description=description,
            color=color or None,
            location=location,
            date=item_date,
            image_filename=image_filename,
            status='active'
        )

        db.session.add(item)
        db.session.commit()
        find_matches(item)

        flash('Lost item report submitted successfully! We also checked for possible matches.', 'success')
        return redirect(url_for('items.item_detail', id=item.id))

    return render_template('report_item.html', item_type='lost', categories=ALLOWED_CATEGORIES)


@items_bp.route('/report/found', methods=['GET', 'POST'])
@login_required
def report_found():
    """Report a found item."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        color = request.form.get('color', '').strip()
        location = request.form.get('location', '').strip()
        date_str = request.form.get('date', '').strip()
        image_file = request.files.get('image')

        # Form Validation
        if not title or not category or not description or not location or not date_str:
            flash('Title, Category, Description, Location, and Date are required.', 'danger')
            return render_template('report_item.html', item_type='found', categories=ALLOWED_CATEGORIES, form_data=request.form)

        if category not in ALLOWED_CATEGORIES:
            flash('Invalid category selected.', 'danger')
            return render_template('report_item.html', item_type='found', categories=ALLOWED_CATEGORIES, form_data=request.form)

        try:
            item_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('report_item.html', item_type='found', categories=ALLOWED_CATEGORIES, form_data=request.form)

        # Handle Optional Image Upload
        image_filename = None
        if image_file and image_file.filename:
            image_filename, err = handle_image_upload(image_file)
            if err:
                flash(err, 'danger')
                return render_template('report_item.html', item_type='found', categories=ALLOWED_CATEGORIES, form_data=request.form)

        # Create Item Record
        item = Item(
            user_id=current_user.id,
            item_type='found',
            title=title,
            category=category,
            description=description,
            color=color or None,
            location=location,
            date=item_date,
            image_filename=image_filename,
            status='active'
        )

        db.session.add(item)
        db.session.commit()
        find_matches(item)

        flash('Found item report submitted successfully! We also checked for possible matches.', 'success')
        return redirect(url_for('items.item_detail', id=item.id))

    return render_template('report_item.html', item_type='found', categories=ALLOWED_CATEGORIES)


@items_bp.route('/lost-items')
def lost_items():
    """Display catalog of active lost items."""
    return _filtered_catalog('lost')


@items_bp.route('/found-items')
def found_items():
    """Display registry of active found items."""
    return _filtered_catalog('found')


def _filtered_catalog(item_type):
    """Public, server-side search and filtering; query values remain visible in UI."""
    query = Item.query.filter_by(item_type=item_type, status='active')
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    location = request.args.get('location', '').strip()
    color = request.args.get('color', '').strip()
    if search:
        term = f'%{search}%'
        query = query.filter(or_(Item.title.ilike(term), Item.description.ilike(term), Item.location.ilike(term)))
    if category in ALLOWED_CATEGORIES:
        query = query.filter(Item.category == category)
    if location:
        query = query.filter(Item.location.ilike(f'%{location}%'))
    if color:
        query = query.filter(Item.color.ilike(f'%{color}%'))
    items = query.order_by(Item.date.desc(), Item.created_at.desc()).all()
    return render_template('items_list.html', items=items, item_type=item_type,
                           title=f'{item_type.capitalize()} Items', categories=ALLOWED_CATEGORIES,
                           filters={'q': search, 'category': category, 'location': location, 'color': color})


@items_bp.route('/item/<int:id>')
def item_detail(id):
    """Detailed item view."""
    item = db.session.get(Item, id)
    if not item:
        return render_template('404.html'), 404
    return render_template('item_detail.html', item=item)


@items_bp.route('/item/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    """Edit an existing item report (Owner only)."""
    item = db.session.get(Item, id)
    if not item:
        return render_template('404.html'), 404

    # Authorization Check
    if item.user_id != current_user.id:
        flash('You are not authorized to edit this item.', 'danger')
        return redirect(url_for('items.item_detail', id=item.id))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        color = request.form.get('color', '').strip()
        location = request.form.get('location', '').strip()
        date_str = request.form.get('date', '').strip()
        image_file = request.files.get('image')

        if not title or not category or not description or not location or not date_str:
            flash('Title, Category, Description, Location, and Date are required.', 'danger')
            return render_template('report_item.html', item=item, is_edit=True, item_type=item.item_type, categories=ALLOWED_CATEGORIES)

        try:
            item_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('report_item.html', item=item, is_edit=True, item_type=item.item_type, categories=ALLOWED_CATEGORIES)

        if image_file and image_file.filename:
            image_filename, err = handle_image_upload(image_file)
            if err:
                flash(err, 'danger')
                return render_template('report_item.html', item=item, is_edit=True, item_type=item.item_type, categories=ALLOWED_CATEGORIES)
            item.image_filename = image_filename

        item.title = title
        item.category = category
        item.description = description
        item.color = color or None
        item.location = location
        item.date = item_date

        db.session.commit()
        flash('Item report updated successfully!', 'success')
        return redirect(url_for('items.item_detail', id=item.id))

    return render_template('report_item.html', item=item, is_edit=True, item_type=item.item_type, categories=ALLOWED_CATEGORIES)


@items_bp.route('/item/<int:id>/resolve', methods=['POST'])
@login_required
def resolve_item(id):
    """Mark an item as resolved or active (Owner only)."""
    item = db.session.get(Item, id)
    if not item:
        return render_template('404.html'), 404

    # Authorization Check
    if item.user_id != current_user.id:
        flash('You are not authorized to modify this item status.', 'danger')
        return redirect(url_for('items.item_detail', id=item.id))

    item.status = 'resolved' if item.status == 'active' else 'active'
    db.session.commit()

    flash(f"Item marked as {item.status}!", 'success')
    return redirect(url_for('items.item_detail', id=item.id))


@items_bp.route('/item/<int:id>/delete', methods=['POST'])
@login_required
def delete_item(id):
    """Delete an item report (Owner only)."""
    item = db.session.get(Item, id)
    if not item:
        return render_template('404.html'), 404

    # Authorization Check
    if item.user_id != current_user.id:
        flash('You are not authorized to delete this item.', 'danger')
        return redirect(url_for('items.item_detail', id=item.id))

    # Delete Image file if present
    if item.image_filename:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.image_filename)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass

    item_type = item.item_type
    db.session.delete(item)
    db.session.commit()

    flash('Item report deleted successfully.', 'success')
    if item_type == 'lost':
        return redirect(url_for('items.lost_items'))
    return redirect(url_for('items.found_items'))
