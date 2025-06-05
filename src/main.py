import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps

# Import models
from src.models.user import db, Business, User, Employee
from src.models.schedule import Shift, ShiftTemplate, TimeOffRequest, Notification

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configure database - Using DATABASE_URL environment variable for Render compatibility
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f"postgresql://{os.getenv('DB_USERNAME', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'postgres')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'crewly_secret_key_for_development')

# Initialize database
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
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
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

# Import routes
from src.routes.auth import auth_bp
from src.routes.business import business_bp
from src.routes.employee import employee_bp
from src.routes.schedule import schedule_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(business_bp, url_prefix='/api/business')
app.register_blueprint(employee_bp, url_prefix='/api/employee')
app.register_blueprint(schedule_bp, url_prefix='/api/schedule')

# Root route
@app.route('/')
def index():
    return jsonify({
        'message': 'Welcome to Crewly API',
        'version': '1.0.0',
        'status': 'running'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
