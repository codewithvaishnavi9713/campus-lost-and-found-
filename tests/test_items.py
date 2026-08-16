import unittest
import os
import sys
import datetime
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.item import Item
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-items-secret-key'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_uploads')

class ItemsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create primary test user
        self.user1 = User(name="Test Owner", email="owner@campus.edu")
        self.user1.set_password("OwnerPassword123")
        db.session.add(self.user1)

        # Create secondary test user (non-owner)
        self.user2 = User(name="Other User", email="other@campus.edu")
        self.user2.set_password("OtherPassword123")
        db.session.add(self.user2)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        # Clean test uploads dir
        if os.path.exists(TestConfig.UPLOAD_FOLDER):
            for f in os.listdir(TestConfig.UPLOAD_FOLDER):
                try:
                    os.remove(os.path.join(TestConfig.UPLOAD_FOLDER, f))
                except OSError:
                    pass

    def login(self, email, password):
        return self.client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_unauthenticated_reporting_access(self):
        """Unauthenticated user cannot access reporting forms."""
        res_lost = self.client.get('/report/lost')
        self.assertEqual(res_lost.status_code, 302)
        self.assertIn('/login', res_lost.headers['Location'])

        res_found = self.client.get('/report/found')
        self.assertEqual(res_found.status_code, 302)
        self.assertIn('/login', res_found.headers['Location'])

    def test_authenticated_report_lost_item(self):
        """Authenticated user can successfully report a lost item with date parsing."""
        self.login('owner@campus.edu', 'OwnerPassword123')

        response = self.client.post('/report/lost', data={
            'title': 'Blue Airpods Pro Case',
            'category': 'Electronics',
            'description': 'Lost near Student Center cafeteria around 2 PM.',
            'color': 'Blue',
            'location': 'Student Center',
            'date': '2026-08-10'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lost item report submitted successfully', response.data)

        # Check DB record
        item = Item.query.filter_by(title='Blue Airpods Pro Case').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.item_type, 'lost')
        self.assertEqual(item.user_id, self.user1.id)
        self.assertIsInstance(item.date, datetime.date)
        self.assertEqual(item.date, datetime.date(2026, 8, 10))

    def test_authenticated_report_found_item(self):
        """Authenticated user can report a found item."""
        self.login('owner@campus.edu', 'OwnerPassword123')

        response = self.client.post('/report/found', data={
            'title': 'Scientific Calculator',
            'category': 'Books & Stationery',
            'description': 'Left on desk in Engineering Room 304.',
            'color': 'Black',
            'location': 'Engineering Building',
            'date': '2026-08-11'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Found item report submitted successfully', response.data)

        item = Item.query.filter_by(title='Scientific Calculator').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.item_type, 'found')

    def test_item_listings_and_detail_view(self):
        """Items appear in correct public listing and detail view."""
        self.login('owner@campus.edu', 'OwnerPassword123')

        # Create lost item
        lost_item = Item(
            user_id=self.user1.id,
            item_type='lost',
            title='Campus ID Badge',
            category='ID Cards & Keys',
            description='Lost near main gate.',
            location='Main Gate',
            date=datetime.date(2026, 8, 12),
            status='active'
        )
        db.session.add(lost_item)
        db.session.commit()

        # Check lost items listing
        res_list = self.client.get('/lost-items')
        self.assertEqual(res_list.status_code, 200)
        self.assertIn(b'Campus ID Badge', res_list.data)

        # Check item detail route
        res_detail = self.client.get(f'/item/{lost_item.id}')
        self.assertEqual(res_detail.status_code, 200)
        self.assertIn(b'Campus ID Badge', res_detail.data)
        self.assertIn(b'Test Owner', res_detail.data)

    def test_owner_edit_resolve_and_delete(self):
        """Item owner can edit, toggle resolve, and delete their item."""
        self.login('owner@campus.edu', 'OwnerPassword123')

        item = Item(
            user_id=self.user1.id,
            item_type='lost',
            title='Leather Wallet',
            category='Bags & Wallets',
            description='Brown leather wallet.',
            location='Library',
            date=datetime.date(2026, 8, 12),
            status='active'
        )
        db.session.add(item)
        db.session.commit()

        # Owner edit
        res_edit = self.client.post(f'/item/{item.id}/edit', data={
            'title': 'Dark Brown Leather Wallet',
            'category': 'Bags & Wallets',
            'description': 'Updated description.',
            'location': 'Library 1st Floor',
            'date': '2026-08-12'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        self.assertIn(b'Item report updated successfully', res_edit.data)

        # Owner resolve
        res_resolve = self.client.post(f'/item/{item.id}/resolve', follow_redirects=True)
        self.assertEqual(res_resolve.status_code, 200)
        self.assertIn(b'resolved', res_resolve.data)

        # Owner delete
        res_delete = self.client.post(f'/item/{item.id}/delete', follow_redirects=True)
        self.assertEqual(res_delete.status_code, 200)
        self.assertIn(b'Item report deleted successfully', res_delete.data)
        self.assertIsNone(db.session.get(Item, item.id))

    def test_non_owner_forbidden_actions(self):
        """Non-owner cannot edit, resolve, or delete someone else's item."""
        # User 1 creates item
        item = Item(
            user_id=self.user1.id,
            item_type='lost',
            title='User1 Umbrella',
            category='Other',
            description='Black umbrella.',
            location='Gym',
            date=datetime.date(2026, 8, 12),
            status='active'
        )
        db.session.add(item)
        db.session.commit()

        # Login as User 2
        self.logout()
        self.login('other@campus.edu', 'OtherPassword123')

        # User 2 attempts edit
        res_edit = self.client.post(f'/item/{item.id}/edit', data={
            'title': 'Hacked Title',
            'category': 'Other',
            'description': 'Hacked',
            'location': 'Gym',
            'date': '2026-08-12'
        }, follow_redirects=True)
        self.assertIn(b'You are not authorized to edit this item', res_edit.data)
        self.assertEqual(db.session.get(Item, item.id).title, 'User1 Umbrella')

        # User 2 attempts resolve
        res_resolve = self.client.post(f'/item/{item.id}/resolve', follow_redirects=True)
        self.assertIn(b'You are not authorized to modify this item status', res_resolve.data)

        # User 2 attempts delete
        res_delete = self.client.post(f'/item/{item.id}/delete', follow_redirects=True)
        self.assertIn(b'You are not authorized to delete this item', res_delete.data)
        self.assertIsNotNone(db.session.get(Item, item.id))

    def test_invalid_image_magic_bytes_rejected(self):
        """File with fake extension but non-image magic bytes is rejected."""
        self.login('owner@campus.edu', 'OwnerPassword123')

        # Create fake PNG file containing plain text / script
        fake_png = (BytesIO(b'<?php echo "evil script"; ?>'), 'malicious.png')

        response = self.client.post('/report/lost', data={
            'title': 'Test Item Bad File',
            'category': 'Electronics',
            'description': 'Testing malicious upload rejection.',
            'location': 'Lab',
            'date': '2026-08-12',
            'image': fake_png
        }, follow_redirects=True)

        self.assertIn(b'File content header validation failed', response.data)
        self.assertIsNone(Item.query.filter_by(title='Test Item Bad File').first())

    def test_valid_image_magic_bytes_accepted(self):
        """File with valid PNG magic bytes is accepted."""
        self.login('owner@campus.edu', 'OwnerPassword123')

        # Valid PNG magic bytes header
        valid_png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4'
        valid_png = (BytesIO(valid_png_bytes), 'item_photo.png')

        response = self.client.post('/report/lost', data={
            'title': 'Valid Photo Item',
            'category': 'Electronics',
            'description': 'Testing valid image upload.',
            'location': 'Lab',
            'date': '2026-08-12',
            'image': valid_png
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lost item report submitted successfully', response.data)

        item = Item.query.filter_by(title='Valid Photo Item').first()
        self.assertIsNotNone(item)
        self.assertIsNotNone(item.image_filename)

if __name__ == '__main__':
    unittest.main()
