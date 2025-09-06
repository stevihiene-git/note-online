# __init__.py - SECURE VERSION
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_migrate import Migrate



db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

def create_app():
     
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Configure for Vercel
    app = Flask(__name__,
                instance_path='/tmp',
                instance_relative_config=True,
                template_folder=os.path.join(BASE_DIR, 'templates'),
                static_folder=os.path.join(BASE_DIR, 'static'))
    
    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
    
    
    
    # Temporarily test without channel_binding
    database_url = os.environ.get('DATABASE_URL', '').replace('&channel_binding=require', '')
    if database_url:
        print(f"Using database URL: {database_url}")  # Add this for debugging
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        print("DATABASE_URL not set, using SQLite")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notedb.db'

    # Get database URL from environment variable
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    
    # Fix for Neon's postgres:// prefix
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Get secret key from environment variable
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key-change-this')
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
     
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Create database tables
    with app.app_context():
        from note_app import models
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Database error: {e}")
    
    # Register blueprints
    from note_app.views import views2
    from note_app.auth import auth2
    from note_app.errors import errors 
    
    app.register_blueprint(views2, url_prefix='/')
    app.register_blueprint(auth2, url_prefix='/')
    app.register_blueprint(errors)
    

    return app

