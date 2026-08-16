import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.config import Config
from app.extensions import db
from app.models.item import Item
from app.models.message import Message
from app.models.user import User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "messages-test-key"


class MessagesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        self.alice = self.make_user("Alice", "alice@campus.edu")
        self.bob = self.make_user("Bob", "bob@campus.edu")
        self.eve = self.make_user("Eve", "eve@campus.edu")
        self.item = Item(user_id=self.bob.id, item_type="found", title="Samsung Phone", category="Electronics",
                         description="Black phone found in science lab.", color="Black", location="Science Lab",
                         date=datetime.date(2026, 8, 16), status="active")
        db.session.add(self.item)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def make_user(self, name, email):
        user = User(name=name, email=email)
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, user):
        return self.client.post("/login", data={"email": user.email, "password": "password123"})

    def logout(self):
        self.client.get("/logout")

    def send_as_alice(self):
        self.login(self.alice)
        return self.client.post(f"/messages/compose/{self.item.id}", data={
            "subject": "Possible match for your phone",
            "body": "Hi! I think this may be my lost phone. Could you confirm the case color?",
        }, follow_redirects=True)

    def test_logged_out_user_cannot_access_inbox(self):
        self.assertEqual(self.client.get("/messages").status_code, 302)

    def test_logged_out_user_cannot_compose(self):
        self.assertEqual(self.client.get(f"/messages/compose/{self.item.id}").status_code, 302)

    def test_user_can_send_message_about_another_users_item(self):
        response = self.send_as_alice()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Message sent securely", response.data)
        self.assertEqual(Message.query.count(), 1)

    def test_sender_receiver_and_related_item_are_stored(self):
        self.send_as_alice()
        message = Message.query.one()
        self.assertEqual(message.sender_id, self.alice.id)
        self.assertEqual(message.receiver_id, self.bob.id)
        self.assertEqual(message.item_id, self.item.id)

    def test_message_appears_in_receivers_inbox(self):
        self.send_as_alice()
        self.logout()
        self.login(self.bob)
        response = self.client.get("/messages")
        self.assertIn(b"Possible match for your phone", response.data)
        self.assertIn(b"Alice", response.data)

    def test_receiver_can_open_and_marks_message_read(self):
        self.send_as_alice()
        message = Message.query.one()
        self.logout()
        self.login(self.bob)
        response = self.client.get(f"/messages/{message.id}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(db.session.get(Message, message.id).is_read)

    def test_receiver_can_reply_and_reply_returns_to_original_sender(self):
        self.send_as_alice()
        original = Message.query.one()
        self.logout()
        self.login(self.bob)
        response = self.client.post(f"/messages/{original.id}/reply", data={"subject": "Re: Possible match", "body": "It has a blue case."})
        self.assertEqual(response.status_code, 302)
        reply = Message.query.filter_by(subject="Re: Possible match").one()
        self.assertEqual(reply.sender_id, self.bob.id)
        self.assertEqual(reply.receiver_id, self.alice.id)
        self.assertEqual(reply.item_id, self.item.id)

    def test_user_cannot_message_themselves(self):
        self.login(self.bob)
        response = self.client.get(f"/messages/compose/{self.item.id}", follow_redirects=True)
        self.assertIn(b"cannot send a message to yourself", response.data)
        self.assertEqual(Message.query.count(), 0)

    def test_user_cannot_read_another_users_message(self):
        self.send_as_alice()
        message = Message.query.one()
        self.logout()
        self.login(self.eve)
        self.assertEqual(self.client.get(f"/messages/{message.id}").status_code, 403)

    def test_user_cannot_delete_another_users_message(self):
        self.send_as_alice()
        message = Message.query.one()
        self.logout()
        self.login(self.eve)
        self.assertEqual(self.client.post(f"/messages/{message.id}/delete").status_code, 403)
        self.assertFalse(db.session.get(Message, message.id).deleted_by_receiver)

    def test_participant_delete_only_hides_own_view(self):
        self.send_as_alice()
        message = Message.query.one()
        self.client.post(f"/messages/{message.id}/delete")
        self.assertTrue(db.session.get(Message, message.id).deleted_by_sender)
        self.logout()
        self.login(self.bob)
        self.assertEqual(self.client.get(f"/messages/{message.id}").status_code, 200)

    def test_resolved_item_cannot_be_contacted(self):
        self.item.status = "resolved"
        db.session.commit()
        self.login(self.alice)
        response = self.client.get(f"/messages/compose/{self.item.id}", follow_redirects=True)
        self.assertIn(b"Only active item reports", response.data)

    def test_compose_validation_enforces_required_and_maximum_values(self):
        self.login(self.alice)
        response = self.client.post(f"/messages/compose/{self.item.id}", data={"subject": "", "body": ""})
        self.assertIn(b"Subject and message are required", response.data)
        response = self.client.post(f"/messages/compose/{self.item.id}", data={"subject": "a" * 151, "body": "valid"})
        self.assertIn(b"Subject must be 150 characters", response.data)

    def test_unread_count_is_shown_and_hides_after_opening(self):
        self.send_as_alice()
        message = Message.query.one()
        self.logout()
        self.login(self.bob)
        dashboard = self.client.get("/dashboard")
        self.assertIn(b"Unread messages: 1", dashboard.data)
        self.client.get(f"/messages/{message.id}")
        dashboard = self.client.get("/dashboard")
        self.assertIn(b"Unread messages: 0", dashboard.data)

    def test_private_email_is_not_rendered_on_message_detail(self):
        self.send_as_alice()
        message = Message.query.one()
        self.logout()
        self.login(self.bob)
        response = self.client.get(f"/messages/{message.id}")
        self.assertNotIn(b"alice@campus.edu", response.data)


if __name__ == "__main__":
    unittest.main()
