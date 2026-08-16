import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.ai.matcher import find_matches
from app.ai.score_utils import category_score, color_score, date_score, location_score
from app.ai.text_similarity import calculate_text_similarity
from app.config import Config
from app.extensions import db
from app.models.item import Item
from app.models.user import User
from app.models.notification import Notification


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "matching-test-key"


class MatchingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        self.user = User(name="Matcher", email="matcher@campus.edu")
        self.user.set_password("password123")
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def item(self, item_type, title="Black Samsung Phone", category="Electronics", description="Black Samsung smartphone with blue protective case.", color="Black", location="Science Lab", day=16, status="active"):
        item = Item(user_id=self.user.id, item_type=item_type, title=title, category=category,
                    description=description, color=color, location=location,
                    date=datetime.date(2026, 8, day), status=status)
        db.session.add(item)
        db.session.commit()
        return item

    def login(self):
        return self.client.post("/login", data={"email": "matcher@campus.edu", "password": "password123"})

    def test_lost_matches_found(self):
        lost = self.item("lost")
        self.item("found", title="Samsung Mobile Phone", description="Black Samsung phone with blue case found near Science Lab.")
        self.assertTrue(find_matches(lost))
        self.assertEqual(Notification.query.count(), 1)

    def test_found_matches_lost(self):
        self.item("lost")
        found = self.item("found", title="Samsung Mobile Phone", description="Black Samsung phone with blue case found near Science Lab.")
        self.assertTrue(find_matches(found))

    def test_same_type_items_do_not_match(self):
        lost = self.item("lost")
        self.item("lost", title="Another Samsung Phone")
        self.assertEqual(find_matches(lost), [])

    def test_resolved_items_are_ignored(self):
        lost = self.item("lost")
        self.item("found", status="resolved")
        self.assertEqual(find_matches(lost), [])

    def test_category_score_affects_result(self):
        self.assertEqual(category_score("Electronics", "Electronics"), 20)
        self.assertEqual(category_score("Electronics", "Bags"), 0)

    def test_color_score_affects_result(self):
        self.assertEqual(color_score("navy", "blue"), 8)
        self.assertEqual(color_score("red", "black"), 0)

    def test_location_score_affects_result(self):
        self.assertEqual(location_score("Science Lab", "Science Lab"), 15)
        self.assertEqual(location_score("Science Lab", "Canteen"), 0)

    def test_date_proximity_affects_result(self):
        self.assertGreater(date_score(datetime.date(2026, 8, 16), datetime.date(2026, 8, 16)),
                           date_score(datetime.date(2026, 8, 16), datetime.date(2026, 8, 24)))

    def test_tfidf_similarity_handles_related_and_empty_text(self):
        self.assertGreater(calculate_text_similarity("black samsung phone", "samsung black phone"), 0.5)
        self.assertEqual(calculate_text_similarity("", "phone"), 0)

    def test_low_scores_are_filtered(self):
        lost = self.item("lost")
        self.item("found", title="Red Backpack", category="Bags & Wallets", description="Large red college backpack.", color="Red", location="Canteen", day=1)
        self.assertEqual(find_matches(lost), [])

    def test_final_scores_are_bounded(self):
        lost = self.item("lost")
        self.item("found", title="Samsung Mobile Phone", description="Black Samsung phone with blue case found near Science Lab.")
        self.assertTrue(all(0 <= result["score"] <= 100 for result in find_matches(lost)))

    def test_results_are_sorted_and_limited_to_ten(self):
        lost = self.item("lost")
        for index in range(12):
            self.item("found", title=f"Samsung Phone {index}", description=f"Black Samsung phone blue case {index}", day=16 if index < 10 else 17)
        results = find_matches(lost)
        self.assertEqual(len(results), 10)
        self.assertEqual([result["score"] for result in results], sorted((result["score"] for result in results), reverse=True))
        self.assertTrue(all(0 <= result["score"] <= 100 for result in results))

    def test_protected_matching_routes_require_login(self):
        item = self.item("lost")
        self.assertEqual(self.client.get(f"/item/{item.id}/matches").status_code, 302)
        self.assertEqual(self.client.post(f"/api/match/run/{item.id}").status_code, 302)

    def test_resolved_source_is_ignored(self):
        source = self.item("lost", status="resolved")
        self.item("found")
        self.assertEqual(find_matches(source), [])

    def test_match_page_and_api_work_when_logged_in(self):
        lost = self.item("lost")
        self.item("found", title="Samsung Mobile Phone", description="Black Samsung phone with blue case found near Science Lab.")
        self.login()
        page = self.client.get(f"/item/{lost.id}/matches")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"AI Possible Matches", page.data)
        response = self.client.post(f"/api/match/run/{lost.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["matches"]), 1)
        match_id = response.get_json()["matches"][0]["id"]
        self.assertEqual(self.client.get(f"/api/match/{match_id}").status_code, 200)


if __name__ == "__main__":
    unittest.main()
