from flask import Blueprint, abort, jsonify, render_template
from flask_login import login_required

from app.ai.matcher import find_matches
from app.extensions import db
from app.models.item import Item
from app.models.match import Match

matching_bp = Blueprint("matching", __name__)


def _match_payload(match):
    return {
        "id": match.id,
        "source_item_id": match.source_item_id,
        "matched_item_id": match.matched_item_id,
        "score": match.score,
        "category_score": match.category_score,
        "color_score": match.color_score,
        "location_score": match.location_score,
        "date_score": match.date_score,
        "text_score": match.text_score,
        "explanation": match.explanation,
    }


@matching_bp.route("/item/<int:id>/matches")
@login_required
def item_matches(id):
    item = db.session.get(Item, id)
    if item is None:
        abort(404)
    results = find_matches(item)
    return render_template("matches.html", item=item, results=results)


@matching_bp.route("/api/match/run/<int:id>", methods=["POST"])
@login_required
def run_matches(id):
    item = db.session.get(Item, id)
    if item is None:
        abort(404)
    results = find_matches(item)
    return jsonify({
        "source_item_id": item.id,
        "matches": [{
            **_match_payload(Match.query.filter_by(source_item_id=item.id, matched_item_id=result["item"].id).first()),
            "matched_item": {"id": result["item"].id, "title": result["item"].title, "item_type": result["item"].item_type},
        } for result in results],
    })


@matching_bp.route("/api/match/<int:id>")
@login_required
def get_match(id):
    match = db.session.get(Match, id)
    if match is None:
        abort(404)
    return jsonify(_match_payload(match))
