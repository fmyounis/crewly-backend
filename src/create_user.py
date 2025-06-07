from src.extensions import db
from src.models import User
from datetime import datetime
from werkzeug.security import generate_password_hash
from src.main import app  # make sure this points to your create_app()

def create_admin_user():
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email='admin@example.com').first()
        if existing_user:
            print('Admin user already exists!')
            return

        # Create new admin user
        user = User(
            business_id=1,
            name='Admin User',
            email='admin@example.com',
            role='admin',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        user.set_password('password123')  # Hash the password

        # Add to database
        db.session.add(user)
        db.session.commit()
        print('Admin user created successfully.')

if __name__ == '__main__':
    create_admin_user()
