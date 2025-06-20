from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.user import db, Business, Employee
from src.main import token_required

business_bp = Blueprint('business', __name__)

@business_bp.route('/', methods=['GET'])
@token_required
def get_business(current_user):
    business = Business.query.filter_by(id=current_user.business_id).first()
    
    if not business:
        return jsonify({'message': 'Business not found!'}), 404
    
    return jsonify({
        'id': business.id,
        'name': business.name,
        'email': business.email,
        'created_at': business.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }), 200

@business_bp.route('/', methods=['PUT'])
@token_required
def update_business(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied!'}), 403
    
    data = request.get_json()
    business = Business.query.filter_by(id=current_user.business_id).first()
    
    if not business:
        return jsonify({'message': 'Business not found!'}), 404
    
    if 'name' in data:
        business.name = data['name']
    
    if 'email' in data:
        existing_business = Business.query.filter_by(email=data['email']).first()
        if existing_business and existing_business.id != business.id:
            return jsonify({'message': 'Email already in use!'}), 409
        
        business.email = data['email']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Business updated successfully!',
        'business': {
            'id': business.id,
            'name': business.name,
            'email': business.email,
            'created_at': business.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200

@business_bp.route('/stats', methods=['GET'])
@token_required
def get_business_stats(current_user):
    business_id = current_user.business_id
    
    employee_count = Employee.query.filter_by(business_id=business_id).count()
    
    current_date = datetime.now()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    from src.models.schedule import Shift, TimeOffRequest
    
    shift_count = Shift.query.filter(
        Shift.business_id == business_id,
        Shift.start_time >= start_of_week,
        Shift.end_time <= end_of_week
    ).count()
    
    pending_requests = TimeOffRequest.query.filter_by(
        business_id=business_id,
        status='pending'
    ).count()
    
    return jsonify({
        'employee_count': employee_count,
        'shift_count': shift_count,
        'pending_requests': pending_requests
    }), 200
