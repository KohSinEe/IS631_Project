"""Script to create the first user."""

from getpass import getpass
from app.database import SessionLocal
from app.models.user import User
from app.models.household import Household
from app.core.security import get_password_hash


def create_first_user():
    """Interactive script to create first user."""
    print("=" * 50)
    print("Create First User")
    print("=" * 50)
    
    # Get user input
    email = input("Email: ").strip()
    name = input("Name (optional): ").strip() or None
    
    while True:
        password = getpass("Password (8-72 chars): ")
        
        # Validate password length
        if len(password) < 8:
            print("❌ Password must be at least 8 characters!")
            continue
        
        if len(password) > 72:
            print("❌ Password must not exceed 72 characters (bcrypt limitation)!")
            continue
        
        if len(password.encode('utf-8')) > 72:
            print("❌ Password is too long when encoded (max 72 bytes)!")
            continue
        
        password_confirm = getpass("Confirm password: ")
        
        if password != password_confirm:
            print("❌ Passwords don't match!")
            continue
        
        # Password is valid
        break
    
    household_name = input("Household name (optional): ").strip() or None
    
    # Create user
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"❌ User with email {email} already exists!")
            return
        
        # Create household if provided
        household_id = None
        if household_name:
            household = Household(name=household_name)
            db.add(household)
            db.flush()
            household_id = household.id
            print(f"✅ Created household: {household_name}")

        # Create user
        user = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(password),
            household_id=household_id,
            is_active=True
        )
        db.add(user)
        db.flush()
        if household_id:
            household = db.query(Household).filter(Household.id == household_id).first()
            if household:
                household.owner_id = user.id
        db.commit()
        
        print("=" * 50)
        print("✅ User created successfully!")
        print(f"   Email: {email}")
        print(f"   Name: {name or 'N/A'}")
        print(f"   Household: {household_name or 'N/A'}")
        print("=" * 50)
        print("\nYou can now login with these credentials.")
        print("Passwords are limited to 72 characters due to bcrypt.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_first_user()