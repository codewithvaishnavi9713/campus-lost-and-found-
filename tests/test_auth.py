import unittest
import os
import sys

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_password_hashing(self):
        """Test that user passwords are securely hashed."""
        user = User(name="Test User", email="test@campus.edu")
        user.set_password("SecretPassword123")
        db.session.add(user)
        db.session.commit()

        # Check password hash is stored
        self.assertNotEqual(user.password_hash, "SecretPassword123")
        self.assertTrue(user.check_password("SecretPassword123"))
        self.assertFalse(user.check_password("WrongPassword"))

    def test_registration_success(self):
        """Test successful registration flow."""
        response = self.client.post('/register', data={
            'name': 'Alice Smith',
            'email': 'alice@campus.edu',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

        # Check user in database
        user = User.query.filter_by(email='alice@campus.edu').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Alice Smith')

    def test_duplicate_email_registration(self):
        """Test rejection of duplicate email address."""
        # Create initial user
        user = User(name="Existing User", email="duplicate@campus.edu")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        # Attempt to register with same email
        response = self.client.post('/register', data={
            'name': 'New User',
            'email': 'duplicate@campus.edu',
            'password': 'password123',
            'confirm_password': 'password123'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'An account with this email address already exists', response.data)

    def test_invalid_login(self):
        """Test login failure with invalid credentials."""
        response = self.client.post('/login', data={
            'email': 'nonexistent@campus.edu',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email address or password', response.data)

    def test_successful_login_and_logout(self):
        """Test complete login, protected dashboard access, and logout flow."""
        # Register user
        user = User(name="Bob Campus", email="bob@campus.edu")
        user.set_password("mysecurepass")
        db.session.add(user)
        db.session.commit()

        # Login
        response = self.client.post('/login', data={
            'email': 'bob@campus.edu',
            'password': 'mysecurepass'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, Bob Campus', response.data)

        # Access protected dashboard
        dashboard_res = self.client.get('/dashboard')
        self.assertEqual(dashboard_res.status_code, 200)
        self.assertIn(b'Bob Campus', dashboard_res.data)

        # Logout
        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn(b'You have been logged out successfully', logout_res.data)

        # Unauthenticated dashboard access should redirect to login
        protected_res = self.client.get('/dashboard')
        self.assertEqual(protected_res.status_code, 302)
        self.assertIn('/login', protected_res.headers['Location'])

if __name__ == '__main__':
    unittest.main()
