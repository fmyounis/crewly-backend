from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.user import db, Employee
from src.models.schedule import Shift, ShiftTemplate, TimeOffRequest
from src.main import token_required

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('/shifts', methods=['GET'])
@token_required
def get_shifts(current_user):
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')
    
    # Base query
    query = Shift.query.filter_by(business_id=current_user.business_id)
    
    # Apply filters
    if start_date:
        query = query.filter(Shift.start_time >= datetime.strptime(start_date, '%Y-%m-%d'))
    
    if end_date:
        query = query.filter(Shift.end_time <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
    
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    
    # Execute query
    shifts = query.all()
    
    # Format results
    output = []
    for shift in shifts:
        employee = Employee.query.filter_by(id=shift.employee_id).first()
        
        shift_data = {
            'id': shift.id,
            'employee_id': shift.employee_id,
            'employee_name': employee.name if employee else 'Unknown',
            'start_time': shift.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': shift.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'role': shift.role,
            'notes': shift.notes
        }
        output.append(shift_data)
    
    return jsonify({'shifts': output}), 200

@schedule_bp.route('/shifts', methods=['POST'])
@token_required
def create_shift(current_user):
    # Check if user has permission (admin or manager)
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'message': 'Permission denied!'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['employee_id', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Check if employee exists and belongs to the business
    employee = Employee.query.filter_by(
        id=data['employee_id'], 
        business_id=current_user.business_id
    ).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found!'}), 404
    
    # Parse dates
    try:
        start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'message': 'Invalid date format! Use YYYY-MM-DD HH:MM:SS'}), 400
    
    # Check if end time is after start time
    if end_time <= start_time:
        return jsonify({'message': 'End time must be after start time!'}), 400
    
    # Check for conflicts
    conflicts = Shift.query.filter_by(employee_id=data['employee_id']).filter(
        ((Shift.start_time <= start_time) & (Shift.end_time > start_time)) |
        ((Shift.start_time < end_time) & (Shift.end_time >= end_time)) |
        ((Shift.start_time >= start_time) & (Shift.end_time <= end_time))
    ).all()
    
    if conflicts:
        return jsonify({'message': 'Shift conflicts with existing shifts!'}), 409
    
    # Create new shift
    new_shift = Shift(
        business_id=current_user.business_id,
        employee_id=data['employee_id'],
        start_time=start_time,
        end_time=end_time,
        role=data.get('role', employee.role),
        notes=data.get('notes', '')
    )
    
    # Add shift to database
    db.session.add(new_shift)
    db.session.commit()
    
    return jsonify({
        'message': 'Shift created successfully!',
        'shift': {
            'id': new_shift.id,
            'employee_id': new_shift.employee_id,
            'employee_name': employee.name,
            'start_time': new_shift.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': new_shift.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'role': new_shift.role,
            'notes': new_shift.notes
        }
    }), 201

@schedule_bp.route('/shifts/<int:shift_id>', methods=['PUT'])
@token_required
def update_shift(current_user, shift_id):
    # Check if user has permission (admin or manager)
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'message': 'Permission denied!'}), 403
    
    # Get shift
    shift = Shift.query.filter_by(
        id=shift_id, 
        business_id=current_user.business_id
    ).first()
    
    if not shift:
        return jsonify({'message': 'Shift not found!'}), 404
    
    data = request.get_json()
    
    # Update employee if provided
    if 'employee_id' in data:
        employee = Employee.query.filter_by(
            id=data['employee_id'], 
            business_id=current_user.business_id
        ).first()
        
        if not employee:
            return jsonify({'message': 'Employee not found!'}), 404
        
        shift.employee_id = data['employee_id']
    
    # Update times if provided
    start_time = shift.start_time
    end_time = shift.end_time
    
    if 'start_time' in data:
        try:
            start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({'message': 'Invalid start time format! Use YYYY-MM-DD HH:MM:SS'}), 400
    
    if 'end_time' in data:
        try:
            end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({'message': 'Invalid end time format! Use YYYY-MM-DD HH:MM:SS'}), 400
    
    # Check if end time is after start time
    if end_time <= start_time:
        return jsonify({'message': 'End time must be after start time!'}), 400
    
    # Check for conflicts
    conflicts = Shift.query.filter_by(employee_id=shift.employee_id).filter(
        Shift.id != shift_id
    ).filter(
        ((Shift.start_time <= start_time) & (Shift.end_time > start_time)) |
        ((Shift.start_time < end_time) & (Shift.end_time >= end_time)) |
        ((Shift.start_time >= start_time) & (Shift.end_time <= end_time))
    ).all()
    
    if conflicts:
        return jsonify({'message': 'Shift conflicts with existing shifts!'}), 409
    
    # Update shift
    shift.start_time = start_time
    shift.end_time = end_time
    
    if 'role' in data:
        shift.role = data['role']
    
    if 'notes' in data:
        shift.notes = data['notes']
    
    db.session.commit()
    
    # Get employee for response
    employee = Employee.query.filter_by(id=shift.employee_id).first()
    
    return jsonify({
        'message': 'Shift updated successfully!',
        'shift': {
            'id': shift.id,
            'employee_id': shift.employee_id,
            'employee_name': employee.name if employee else 'Unknown',
            'start_time': shift.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': shift.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'role': shift.role,
            'notes': shift.notes
        }
    }), 200

@schedule_bp.route('/shifts/<int:shift_id>', methods=['DELETE'])
@token_required
def delete_shift(current_user, shift_id):
    # Check if user has permission (admin or manager)
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'message': 'Permission denied!'}), 403
    
    # Get shift
    shift = Shift.query.filter_by(
        id=shift_id, 
        business_id=current_user.business_id
    ).first()
    
    if not shift:
        return jsonify({'message': 'Shift not found!'}), 404
    
    # Delete shift
    db.session.delete(shift)
    db.session.commit()
    
    return jsonify({'message': 'Shift deleted successfully!'}), 200

@schedule_bp.route('/shift-types', methods=['GET'])
@token_required
def get_shift_templates(current_user):
    # Get all shift templates for the business
    templates = ShiftTemplate.query.filter_by(business_id=current_user.business_id).all()
    
    output = []
    for template in templates:
        template_data = {
            'id': template.id,
            'name': template.name,
            'start_time': template.start_time.strftime('%H:%M:%S'),
            'end_time': template.end_time.strftime('%H:%M:%S'),
            'days_of_week': template.days_of_week,
            'role': template.role
        }
        output.append(template_data)
    
    return jsonify({'shift_types': output}), 200

@schedule_bp.route('/shift-types', methods=['POST'])
@token_required
def create_shift_template(current_user):
    # Check if user has permission (admin or manager)
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'message': 'Permission denied!'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Parse times
    try:
        start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M:%S').time()
    except ValueError:
        return jsonify({'message': 'Invalid time format! Use HH:MM:SS'}), 400
    
    # Create new shift template
    new_template = ShiftTemplate(
        business_id=current_user.business_id,
        name=data['name'],
        start_time=start_time,
        end_time=end_time,
        days_of_week=data.get('days_of_week', ''),
        role=data.get('role', '')
    )
    
    # Add template to database
    db.session.add(new_template)
    db.session.commit()
    
    return jsonify({
        'message': 'Shift type created successfully!',
        'shift_type': {
            'id': new_template.id,
            'name': new_template.name,
            'start_time': new_template.start_time.strftime('%H:%M:%S'),
            'end_time': new_template.end_time.strftime('%H:%M:%S'),
            'days_of_week': new_template.days_of_week,
            'role': new_template.role
        }
    }), 201
