from flask import Flask
from src.models import db  # <-- from init now, not user
from src.routes.auth import auth_bp

app = Flask(__name__)

# Configure your database URI (example with SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crewly.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret key for JWT
app.config['SECRET_KEY'] = 'Ffmonday$321'

# Initialize the database with app
db.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates tables if missing
    app.run(debug=True)
