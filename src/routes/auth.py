from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from src.models.user import db, Business, User
from src.main import app

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if business already exists
    if Business.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Business already exists!'}), 409
    
    # Create new business
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_business = Business(
        name=data['name'],
        email=data['email'],
        password=hashed_password
    )
    
    # Add business to database
    db.session.add(new_business)
    db.session.commit()
    
    # Create admin user for the business
    admin_user = User(
        business_id=new_business.id,
        name=f"{data['name']} Admin",
        email=data['email'],
        password=hashed_password,
        role='admin'
    )
    
    # Add admin user to database
    db.session.add(admin_user)
    db.session.commit()
    
    return jsonify({'message': 'Business registered successfully!'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Check if user exists
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'message': 'Invalid credentials!'}), 401
    
    # Check password
    if check_password_hash(user.password, data['password']):
        # Generate token
        token = jwt.encode({
            'user_id': user.id,
            'business_id': user.business_id,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
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
    
    return jsonify({'message': 'Invalid credentials!'}), 401

@auth_bp.route('/user', methods=['GET'])
def get_user():
    token = None
    
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401
    
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = User.query.filter_by(id=data['user_id']).first()
        
        if not current_user:
            return jsonify({'message': 'User not found!'}), 404
        
        return jsonify({
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'role': current_user.role,
            'business_id': current_user.business_id
        }), 200
    except:
        return jsonify({'message': 'Token is invalid!'}), 401
