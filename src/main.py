from flask import Flask
from src.models.user import db
from src.routes.auth import auth_bp

app = Flask(__name__)

# Configure your database URI (example with SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crewly.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set your secret key for JWT
app.config['SECRET_KEY'] = 'Ffmonday$321'

# Initialize the database with app
db.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
