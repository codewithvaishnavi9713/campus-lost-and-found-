"""Database-backed matching service for active lost and found reports."""

from flask import current_app

from app.ai.image_similarity import image_similarity
from app.ai.score_utils import category_score, color_score, date_score, location_score, text_score
from app.extensions import db
from app.models.item import Item
from app.models.match import Match
from app.models.notification import Notification

MINIMUM_MATCH_SCORE = 40
MAX_MATCHES = 10


def _explanation(scores):
    strengths, details = [], []
    if scores["category"] == 20:
        strengths.append("category")
        details.append("same category")
    if scores["color"] >= 8:
        strengths.append("color")
        details.append("similar colour")
    if scores["location"] >= 10:
        strengths.append("location")
        details.append("nearby location")
    if scores["date"] >= 8:
        strengths.append("date")
        details.append("close dates")
    if scores["text"] >= 25:
        strengths.append("description")
        details.append("overlapping description terms")
    if strengths:
        return "Why this surfaced: " + ", ".join(details) + ". Review item details before contacting the reporter."
    return "Some report details are similar; review the item details before making contact."


def _result_for(source, candidate):
    scores = {
        "category": category_score(source.category, candidate.category),
        "color": color_score(source.color, candidate.color),
        "location": location_score(source.location, candidate.location),
        "date": date_score(source.date, candidate.date),
        "text": text_score(source.title, source.description, candidate.title, candidate.description),
    }
    visual_score = image_similarity(source, candidate, current_app.config.get("IMAGE_SIMILARITY_ENABLED", False))
    total = round(max(0, min(100, sum(scores.values()))), 2)
    return {"item": candidate, "score": total, "scores": scores, "visual_score": visual_score, "explanation": _explanation(scores)}


def find_matches(item):
    """Find and persist the best active reports of the opposite type for *item*."""
    if item.status != "active" or item.item_type not in {"lost", "found"}:
        return []

    opposite_type = "found" if item.item_type == "lost" else "lost"
    candidates = Item.query.filter(
        Item.item_type == opposite_type,
        Item.status == "active",
        Item.id != item.id,
    ).all()
    results = [_result_for(item, candidate) for candidate in candidates]
    results = [result for result in results if result["score"] >= MINIMUM_MATCH_SCORE]
    results.sort(key=lambda result: result["score"], reverse=True)
    results = results[:MAX_MATCHES]

    for result in results:
        record = Match.query.filter_by(source_item_id=item.id, matched_item_id=result["item"].id).first()
        is_new = record is None
        if record is None:
            record = Match(source_item_id=item.id, matched_item_id=result["item"].id)
            db.session.add(record)
        record.score = result["score"]
        record.category_score = result["scores"]["category"]
        record.color_score = result["scores"]["color"]
        record.location_score = result["scores"]["location"]
        record.date_score = result["scores"]["date"]
        record.text_score = result["scores"]["text"]
        record.explanation = result["explanation"]
        if is_new:
            db.session.flush()
            notified_user_ids = set()
            for report in (item, result["item"]):
                if report.user_id in notified_user_ids:
                    continue
                notified_user_ids.add(report.user_id)
                db.session.add(Notification(
                    user_id=report.user_id,
                    item_id=report.id,
                    match_id=record.id,
                    message=f"Possible {round(result['score'])}% match for your {report.item_type} report: {report.title}",
                ))
    db.session.commit()
    return results
