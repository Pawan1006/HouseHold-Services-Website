from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

# Initialize the SQLAlchemy object for database interactions
db = SQLAlchemy()
DB_NAME = "database.db" # Define the name of the database file

def create_app():
    # Create an instance of the Flask application
    app = Flask(__name__)

    # Configure the app's secret key and database URI
    app.config["SECRET_KEY"] = "qwerty"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"
    
    # Initialize the SQLAlchemy instance with the app
    db.init_app(app)

    # Import views and authentication blueprints
    from .views import views
    from .auth import auth

    # Register the blueprints with specified URL prefixes
    app.register_blueprint(views, url_prefix = '/')
    app.register_blueprint(auth, url_prefix = '/')

    # Import the database models
    from .models import User, Professional, Admin
    
    # Create the database tables if they don't exist
    with app.app_context():
        db.create_all()
        print("Created Database!")
        
        # Check if the admin user already exists
        admin = Admin.query.filter_by(email="admin@gmail.com").first()
        if not admin:
            admin = Admin(email="admin@gmail.com", password=124578)
            db.session.add(admin)
            db.session.commit()
    
    # Initialize the LoginManager for user authentication
    login_manager = LoginManager()
    login_manager.login_view = "auth.login" # Login view for redirection
    login_manager.init_app(app) # Initialize the LoginManager with the app

    @login_manager.user_loader
    def load_user(id):
        # Attempt to find the user in User model
        user = User.query.get(int(id))
        if user:
            return user
    
        # Attempt to find the user in Professional model
        professional = Professional.query.get(int(id))
        if professional:
            return professional
        
        # Attempt to find the user in the Admin model
        admin = Admin.query.get(int(id))
        if admin:
            return admin
    
        # If not found in either model
        return None

    return app
