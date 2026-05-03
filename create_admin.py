from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash


def create_first_admin():
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.role == "admin").first()
        if existing_admin:
            print(f"Администратор уже существует: {existing_admin.username}")
            return

        username = input("Введите имя пользователя администратора: ") or "admin"
        password = input("Введите пароль: ") or "admin123"
        full_name = input("Введите ФИО: ") or "Главный Администратор"
        email = input("Введите email: ") or "admin@club.com"

        admin = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role="admin"
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("\nАдминистратор успешно создан!")
        print(f"Логин: {username}")
        print(f"Пароль: {password}")
        print("Роль: ADMIN")

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_first_admin()
