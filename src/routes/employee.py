from flask import Blueprint, request, jsonify
from src.models.user import db, Employee
from src.main import token_required

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/', methods=['GET'])
@token_required
def get_employees(current_user):
    employees = Employee.query.filter_by(business_id=current_user.business_id).all()
    
    output = []
    for employee in employees:
        employee_data = {
            'id': employee.id,
            'name': employee.name,
            'email': employee.email,
            'phone': employee.phone,
            'role': employee.role,
            'created_at': employee.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        output.append(employee_data)
    
    return jsonify({'employees': output}), 200

@employee_bp.route('/<int:employee_id>', methods=['GET'])
@token_required
def get_employee(current_user, employee_id):
    employee = Employee.query.filter_by(
        id=employee_id, 
        business_id=current_user.business_id
    ).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found!'}), 404
    
    employee_data = {
        'id': employee.id,
        'name': employee.name,
        'email': employee.email,
        'phone': employee.phone,
        'role': employee.role,
        'created_at': employee.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return jsonify({'employee': employee_data}), 200

@employee_bp.route('/', methods=['POST'])
@token_required
def create_employee(current_user):
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'message': 'Permission denied!'}), 403
    
    data = request.get_json()
    required_fields = ['name', 'email', 'role']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    new_employee = Employee(
        business_id=current_user.business_id,
        name=data['name'],
        email=data['email'],
        role=data['role'],
        phone=data.get('phone', '')
    )
    
    db.session.add(new_employee)
    db.session.commit()
    
    return jsonify({
        'message': 'Employee created successfully!',
        'employee': {
            'id': new_employee.id,
            'name': new_employee.name,
            'email': new_employee.email,
            'phone': new_employee.phone,
            'role': new_employee.role
        }
    }), 201

@employee_bp.route('/<int:employee_id>', methods=['PUT'])
@token_required
def update_employee(current_user, employee_id):
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'message': 'Permission denied!'}), 403
    
    employee = Employee.query.filter_by(
        id=employee_id, 
        business_id=current_user.business_id
    ).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found!'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        employee.name = data['name']
    if 'email' in data:
        employee.email = data['email']
    if 'phone' in data:
        employee.phone = data['phone']
    if 'role' in data:
        employee.role = data['role']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Employee updated successfully!',
        'employee': {
            'id': employee.id,
            'name': employee.name,
            'email': employee.email,
            'phone': employee.phone,
            'role': employee.role
        }
    }), 200

@employee_bp.route('/<int:employee_id>', methods=['DELETE'])
@token_required
def delete_employee(current_user, employee_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied!'}), 403
    
    employee = Employee.query.filter_by(
        id=employee_id, 
        business_id=current_user.business_id
    ).first()
    
    if not employee:
        return jsonify({'message': 'Employee not found!'}), 404
    
    db.session.delete(employee)
    db.session.commit()
    
    return jsonify({'message': 'Employee deleted successfully!'}), 200
