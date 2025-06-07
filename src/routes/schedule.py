from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
from src.models.user import db, Employee
from src.models.schedule import Shift, ShiftTemplate, TimeOffRequest
from src.utils.auth import token_required


schedule_bp = Blueprint('schedule', __name__)

def has_permission(user):
    return user.role in ['admin', 'manager']

def parse_datetime(dt_str, fmt='%Y-%m-%d %H:%M:%S'):
    """Parse datetime string and return UTC-aware datetime."""
    try:
        # Assume input is in UTC; adjust if needed
        dt_naive = datetime.strptime(dt_str, fmt)
        return dt_naive.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def parse_time(t_str):
    """Parse time string into a time object."""
    try:
        return datetime.strptime(t_str, '%H:%M:%S').time()
    except Exception:
        return None

@schedule_bp.route('/shifts', methods=['GET'])
@token_required
def get_shifts(current_user):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=50, type=int)

    query = Shift.query.filter_by(business_id=current_user.business_id)

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            query = query.filter(Shift.start_time >= start_dt)
        except ValueError:
            return jsonify({'message': 'Invalid start_date format! Use YYYY-MM-DD'}), 400

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1)
            query = query.filter(Shift.end_time <= end_dt)
        except ValueError:
            return jsonify({'message': 'Invalid end_date format! Use YYYY-MM-DD'}), 400

    if employee_id:
        if not employee_id.isdigit():
            return jsonify({'message': 'Invalid employee_id! Must be integer.'}), 400
        query = query.filter_by(employee_id=int(employee_id))

    # Pagination
    shifts_paginated = query.order_by(Shift.start_time).paginate(page=page, per_page=per_page, error_out=False)
    shifts = shifts_paginated.items

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

    return jsonify({
        'shifts': output,
        'page': page,
        'per_page': per_page,
        'total': shifts_paginated.total
    }), 200

@schedule_bp.route('/shifts', methods=['POST'])
@token_required
def create_shift(current_user):
    if not has_permission(current_user):
        return jsonify({'message': 'Permission denied!'}), 403

    data = request.get_json()

    # Validate required fields
    required_fields = ['employee_id', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400

    # Validate employee_id type
    try:
        employee_id = int(data['employee_id'])
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid employee_id! Must be an integer.'}), 400

    employee = Employee.query.filter_by(id=employee_id, business_id=current_user.business_id).first()
    if not employee:
        return jsonify({'message': 'Employee not found!'}), 404

    start_time = parse_datetime(data['start_time'])
    end_time = parse_datetime(data['end_time'])
    if not start_time or not end_time:
        return jsonify({'message': 'Invalid date format! Use YYYY-MM-DD HH:MM:SS'}), 400

    if end_time <= start_time:
        return jsonify({'message': 'End time must be after start time!'}), 400

    conflicts = Shift.query.filter_by(employee_id=employee_id).filter(
        Shift.start_time < end_time,
        Shift.end_time > start_time
    ).all()

    if conflicts:
        return jsonify({'message': 'Shift conflicts with existing shifts!'}), 409

    new_shift = Shift(
        business_id=current_user.business_id,
        employee_id=employee_id,
        start_time=start_time,
        end_time=end_time,
        role=data.get('role', employee.role),
        notes=data.get('notes', '')
    )

    try:
        db.session.add(new_shift)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Database error: could not create shift.'}), 500

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
    if not has_permission(current_user):
        return jsonify({'message': 'Permission denied!'}), 403

    shift = Shift.query.filter_by(id=shift_id, business_id=current_user.business_id).first()
    if not shift:
        return jsonify({'message': 'Shift not found!'}), 404

    data = request.get_json()

    if 'employee_id' in data:
        try:
            new_employee_id = int(data['employee_id'])
        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid employee_id! Must be an integer.'}), 400

        employee = Employee.query.filter_by(id=new_employee_id, business_id=current_user.business_id).first()
        if not employee:
            return jsonify({'message': 'Employee not found!'}), 404

        shift.employee_id = new_employee_id
    else:
        employee = Employee.query.filter_by(id=shift.employee_id).first()

    start_time = shift.start_time
    end_time = shift.end_time

    if 'start_time' in data:
        dt = parse_datetime(data['start_time'])
        if not dt:
            return jsonify({'message': 'Invalid start time format! Use YYYY-MM-DD HH:MM:SS'}), 400
        start_time = dt

    if 'end_time' in data:
        dt = parse_datetime(data['end_time'])
        if not dt:
            return jsonify({'message': 'Invalid end time format! Use YYYY-MM-DD HH:MM:SS'}), 400
        end_time = dt

    if end_time <= start_time:
        return jsonify({'message': 'End time must be after start time!'}), 400

    conflicts = Shift.query.filter_by(employee_id=shift.employee_id).filter(
        Shift.id != shift_id,
        Shift.start_time < end_time,
        Shift.end_time > start_time
    ).all()

    if conflicts:
        return jsonify({'message': 'Shift conflicts with existing shifts!'}), 409

    shift.start_time = start_time
    shift.end_time = end_time

    if 'role' in data:
        shift.role = data['role']

    if 'notes' in data:
        shift.notes = data['notes']

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Database error: could not update shift.'}), 500

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
    if not has_permission(current_user):
        return jsonify({'message': 'Permission denied!'}), 403

    shift = Shift.query.filter_by(id=shift_id, business_id=current_user.business_id).first()
    if not shift:
        return jsonify({'message': 'Shift not found!'}), 404

    try:
        db.session.delete(shift)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Database error: could not delete shift.'}), 500

    return jsonify({'message': 'Shift deleted successfully!'}), 200

@schedule_bp.route('/shift-types', methods=['GET'])
@token_required
def get_shift_templates(current_user):
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
    if not has_permission(current_user):
        return jsonify({'message': 'Permission denied!'}), 403

    data = request.get_json()
    required_fields = ['name', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400

    start_time = parse_time(data['start_time'])
    end_time = parse_time(data['end_time'])
    if not start_time or not end_time:
        return jsonify({'message': 'Invalid time format! Use HH:MM:SS'}), 400

    new_template = ShiftTemplate(
        business_id=current_user.business_id,
        name=data['name'],
        start_time=start_time,
        end_time=end_time,
        days_of_week=data.get('days_of_week', ''),
        role=data.get('role', '')
    )

    try:
        db.session.add(new_template)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Database error: could not create shift type.'}), 500

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
