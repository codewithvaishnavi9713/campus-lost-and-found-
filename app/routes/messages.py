from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.item import Item
from app.models.message import Message

messages_bp = Blueprint("messages", __name__)

DEFAULT_SUBJECT = "Possible match for your item"
DEFAULT_BODY = (
    "Hi! I think I may have found a possible match for this item. Could you please "
    "confirm a few details so we can verify it?"
)
MAX_SUBJECT_LENGTH = 150
MAX_BODY_LENGTH = 2000


def _participant_message(message_id):
    """Return a visible message only when the current user is a participant."""
    message = db.session.get(Message, message_id)
    if message is None:
        abort(404)
    if current_user.id not in (message.sender_id, message.receiver_id):
        abort(403)
    if ((message.sender_id == current_user.id and message.deleted_by_sender) or
            (message.receiver_id == current_user.id and message.deleted_by_receiver)):
        abort(404)
    return message


def _validated_content(subject, body):
    subject, body = subject.strip(), body.strip()
    if not subject or not body:
        return None, "Subject and message are required."
    if len(subject) > MAX_SUBJECT_LENGTH:
        return None, f"Subject must be {MAX_SUBJECT_LENGTH} characters or fewer."
    if len(body) > MAX_BODY_LENGTH:
        return None, f"Message must be {MAX_BODY_LENGTH} characters or fewer."
    return (subject, body), None


@messages_bp.route("/messages")
@login_required
def inbox():
    received = Message.query.filter_by(receiver_id=current_user.id, deleted_by_receiver=False).order_by(
        Message.created_at.desc()
    ).all()
    return render_template("messages.html", messages=received)


@messages_bp.route("/messages/<int:id>")
@login_required
def message_detail(id):
    message = _participant_message(id)
    if message.receiver_id == current_user.id and not message.is_read:
        message.is_read = True
        db.session.commit()
    return render_template("message_detail.html", message=message)


@messages_bp.route("/messages/compose/<int:item_id>", methods=["GET", "POST"])
@login_required
def compose(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)
    if item.status != "active":
        flash("Only active item reports can be contacted.", "warning")
        return redirect(url_for("items.item_detail", id=item.id))
    if item.user_id == current_user.id:
        flash("You cannot send a message to yourself.", "warning")
        return redirect(url_for("items.item_detail", id=item.id))

    if request.method == "POST":
        content, error = _validated_content(request.form.get("subject", ""), request.form.get("body", ""))
        if error:
            flash(error, "danger")
            return render_template("compose_message.html", item=item, subject=request.form.get("subject", ""), body=request.form.get("body", ""))
        subject, body = content
        message = Message(sender_id=current_user.id, receiver_id=item.user_id, item_id=item.id,
                          subject=subject, body=body)
        db.session.add(message)
        db.session.commit()
        flash("Message sent securely through Campus Lost & Found.", "success")
        return redirect(url_for("messages.inbox"))

    return render_template("compose_message.html", item=item, subject=DEFAULT_SUBJECT, body=DEFAULT_BODY)


@messages_bp.route("/messages/<int:id>/reply", methods=["POST"])
@login_required
def reply(id):
    original = _participant_message(id)
    receiver_id = original.sender_id if current_user.id == original.receiver_id else original.receiver_id
    if receiver_id == current_user.id:
        abort(400)
    content, error = _validated_content(request.form.get("subject", ""), request.form.get("body", ""))
    if error:
        flash(error, "danger")
        return redirect(url_for("messages.message_detail", id=original.id))
    subject, body = content
    message = Message(sender_id=current_user.id, receiver_id=receiver_id, item_id=original.item_id,
                      subject=subject, body=body)
    db.session.add(message)
    db.session.commit()
    flash("Reply sent securely.", "success")
    return redirect(url_for("messages.inbox"))


@messages_bp.route("/messages/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    message = _participant_message(id)
    if message.sender_id == current_user.id:
        message.deleted_by_sender = True
    else:
        message.deleted_by_receiver = True
    db.session.commit()
    flash("Message removed from your view.", "info")
    return redirect(url_for("messages.inbox"))
