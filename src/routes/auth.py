from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from src.models.user import db, Business, User
from src.utils.auth_decorators import token_required  # import from new location

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not all(k in data for k in ('name', 'email', 'password')):
        return jsonify({'message': 'Missing required fields!'}), 400

    # Check if business already exists by name or email
    if Business.query.filter((Business.email == data['email']) | (Business.name == data['name'])).first():
        return jsonify({'message': 'Business already exists!'}), 409

    # Create new business
    new_business = Business(
        name=data['name'],
        email=data['email']
    )
    db.session.add(new_business)
    db.session.commit()

    # Create admin user for the business
    admin_user = User(
        business_id=new_business.id,
        name=f"{data['name']} Admin",
        email=data['email'],
        role='admin'
    )
    admin_user.set_password(data['password'])  # Hash password

    db.session.add(admin_user)
    db.session.commit()

    return jsonify({'message': 'Business registered successfully!'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not all(k in data for k in ('email', 'password')):
        return jsonify({'message': 'Missing email or password!'}), 400

    # Check if user exists
    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials!'}), 401

    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'business_id': user.business_id,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        'message': 'Login successful!',
        'token': token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'business_id': user.business_id
        }
    }), 200


@auth_bp.route('/user', methods=['GET'])
@token_required
def get_user(current_user):
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'role': current_user.role,
        'business_id': current_user.business_id
    }), 200


# Route to create a test user and business for initial testing
@auth_bp.route('/create_test_user', methods=['POST'])
def create_test_user():
    # Check if test business already exists
    test_business = Business.query.filter_by(email='test@example.com').first()
    if test_business:
        return jsonify({'message': 'Test business already exists!'}), 409

    # Create test business
    test_business = Business(
        name='Test Business',
        email='test@example.com'
    )
    db.session.add(test_business)
    db.session.commit()

    # Create test admin user
    test_user = User(
        business_id=test_business.id,
        name='Test User',
        email='test@example.com',
        role='admin'
    )
    test_user.set_password('password123')
    db.session.add(test_user)
    db.session.commit()

    return jsonify({'message': 'Test business and user created successfully!'}), 201
