from flask import Flask
from flask_cors import CORS
from src.extensions import db
from src.models import *  # Imports Business, User, Employee, Shift, ShiftTemplate, TimeOffRequest, Notification
from src.routes.auth import auth_bp
from src.routes.schedule import schedule_bp

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crewly.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'loveThis'

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(schedule_bp, url_prefix='/schedule')

    # Health check route
    @app.route('/health')
    def health_check():
        return {'status': 'running'}

    with app.app_context():
        db.create_all()  # Create tables if they don't exist

    return app

# Gunicorn entrypoint
app = create_app()

# CLI run support
if __name__ == '__main__':
    app.run(debug=True, port=8000)
