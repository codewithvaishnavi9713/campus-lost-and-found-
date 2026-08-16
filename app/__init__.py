from flask import Flask
from app.config import Config
from app.extensions import db, login_manager

def create_app(config_class=Config):
    """Flask Application Factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)

    # User Loader Callback for Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Blueprints
    from app.routes import main_bp
    from app.routes.auth import auth_bp
    from app.routes.items import items_bp
    from app.routes.matching import matching_bp
    from app.routes.admin import admin_bp
    from app.routes.messages import messages_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(messages_bp)

    @app.context_processor
    def inject_message_count():
        """Provide a safe unread count to authenticated navigation templates."""
        from flask_login import current_user
        from app.models.message import Message
        if not current_user.is_authenticated:
            return {"unread_message_count": 0}
        return {"unread_message_count": Message.query.filter_by(
            receiver_id=current_user.id, is_read=False, deleted_by_receiver=False
        ).count()}

    # Create Database Tables
    with app.app_context():
        db.create_all()

    return app
