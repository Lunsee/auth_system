import logging
from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal, Base


from app.models import Base, User, Role, Permission, user_role, role_permission
from app.auth import hash_password_bcrypt

logger = logging.getLogger(__name__)


def create_tables():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully")


def create_initial_data(db: Session):
    logger.info("Creating initial data...")

    # All Permissions
    permissions_data = [
        {"name": "user:read", "description": "Чтение данных пользователей"},
        {"name": "user:write", "description": "Создание и изменение пользователей"},
        {"name": "user:delete", "description": "Удаление пользователей"},
        {"name": "role:manage", "description": "Управление ролями и правами"},
        {"name": "content:read", "description": "Чтение контента"},
        {"name": "content:write", "description": "Создание и изменение контента"},
        {"name": "content:delete", "description": "Удаление контента"},
    ]

    permissions = {}
    for perm_data in permissions_data:
        existing_perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing_perm:
            permission = Permission(**perm_data)
            db.add(permission)
            permissions[perm_data["name"]] = permission
        else:
            permissions[perm_data["name"]] = existing_perm

    db.commit()
    logger.info("Permissions created")

    #Roles
    roles_data = [
        {
            "name": "admin",
            "description": "Администратор системы - полный доступ",
            "permissions": list(permissions.values())  # Все права
        },
        {
            "name": "moderator",
            "description": "Модератор - управление контентом",
            "permissions": [
                permissions["user:read"],
                permissions["content:read"],
                permissions["content:write"],
                permissions["content:delete"]
            ]
        },
        {
            "name": "user",
            "description": "Обычный пользователь",
            "permissions": [
               #permissions["user:read"],
                permissions["content:read"],
                permissions["content:write"]
            ]
        },
        {
            "name": "guest",
            "description": "Гость - минимальные права",
            "permissions": [
                permissions["content:read"]
            ]
        }
    ]

    roles = {}
    for role_data in roles_data:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(name=role_data["name"], description=role_data["description"])
            role.permissions = role_data["permissions"]
            db.add(role)
            roles[role_data["name"]] = role
        else:
            roles[role_data["name"]] = existing_role

    db.commit()
    logger.info("Roles created with permissions")

    users_data = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "first_name": "Алексей",
            "last_name": "Петров",
            "middle_name": "Иванович",
            "password": "admin123",
            "roles": [roles["admin"]],
            "is_active": True
        },
        {
            "username": "moderator_user",
            "email": "moderator@example.com",
            "first_name": "Мария",
            "last_name": "Сидорова",
            "password": "moderator123",
            "roles": [roles["moderator"]],
            "is_active": True
        },
        {
            "username": "regular_user",
            "email": "user@example.com",
            "first_name": "Иван",
            "last_name": "Иванов",
            "password": "user123",
            "roles": [roles["user"]],
            "is_active": True
        },
        {
            "username": "inactive_user",
            "email": "inactive@example.com",
            "first_name": "Ольга",
            "last_name": "Смирнова",
            "password": "user123",
            "roles": [roles["user"]],
            "is_active": False
        },
        {
            "username": "multi_role_user",
            "email": "multi@example.com",
            "first_name": "Дмитрий",
            "last_name": "Кузнецов",
            "password": "user123",
            "roles": [roles["user"], roles["moderator"]],
            "is_active": True
        }
    ]

    for user_data in users_data:
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing_user:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                middle_name=user_data.get("middle_name"),
                password_hash=hash_password_bcrypt(user_data["password"]),
                is_active=user_data["is_active"]
            )
            user.roles = user_data["roles"]
            db.add(user)

    db.commit()
    logger.info("Test users created")

    print("\n" + "=" * 50)
    print(" INITIAL DATA CREATED SUCCESSFULLY!")
    print("=" * 50)
    print("\n TEST USERS (для ручного тестирования):")
    print("-" * 30)

    test_users = [
        {"username": "admin", "password": "admin123", "description": " Полный доступ ко всему"},
        {"username": "moderator_user", "password": "moderator123", "description": " Может управлять контентом"},
        {"username": "regular_user", "password": "user123", "description": " Обычный пользователь"},
        {"username": "multi_role_user", "password": "user123", "description": " Пользователь + модератор"},
        {"username": "inactive_user", "password": "user123", "description": " Неактивный пользователь"}
    ]

    for user in test_users:
        print(f"👤{user['username']}")
        print(f"    Password: {user['password']}")
        print(f"    {user['description']}")
        print()

    print(" PERMISSIONS SUMMARY:")
    print("-" * 25)
    for role_name, role in roles.items():
        perm_names = [perm.name for perm in role.permissions]
        print(f" {role_name}: {', '.join(perm_names)}")

    print("\n Для тестирования используйте:")
    print("   POST /auth/token - для получения токена")
    print("   GET /users/me - для проверки профиля")
    print("   GET /users/ - для списка пользователей (только админ)")
    print("=" * 50)


def init_db():
    db = SessionLocal()
    try:
        create_tables()
        create_initial_data(db)
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        print("✅ Database initialization completed!")