from flask import Flask, jsonify
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


# JWT token_required decorator
from functools import wraps
from flask import request
import jwt
from src.models.user import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # JWT token is expected in the Authorization header as Bearer token
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired! Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
