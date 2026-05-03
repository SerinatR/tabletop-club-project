import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine


# Тестовая база данных
@pytest.fixture(scope="module")
def test_client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client = TestClient(app)

    admin_response = client.post("/register", json={
        "username": "admin",
        "email": "admin@club.com",
        "password": "admin",
        "full_name": "Главный Администратор"
    })
    assert admin_response.status_code == 200

    from app.database import SessionLocal
    from app.models import User
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        admin.role = "admin"
        db.commit()
    db.close()

    client.post("/register", json={
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "123456",
        "full_name": "Тестовый Пользователь"
    })

    token = client.post("/token", data={"username": "admin", "password": "admin"}).json()["access_token"]
    client.post(
        "/games/",
        json={
            "name": "Catan",
            "min_players": 3,
            "max_players": 4,
            "duration": 90,
            "category": "strategy",
            "description": "Классика",
            "total_quantity": 2
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    yield client
    Base.metadata.drop_all(bind=engine)


def test_register_user(test_client):
    response = test_client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "123456",
        "full_name": "Тестовый Пользователь"
    })
    assert response.status_code == 200


def test_register_duplicate_username(test_client):
    response = test_client.post("/register", json={
        "username": "testuser",  # уже существует
        "email": "new@example.com",
        "password": "123456",
        "full_name": "Дубликат"
    })
    assert response.status_code == 400
    assert "Имя пользователя уже занято" in response.json()["detail"]


def test_register_duplicate_email(test_client):
    response = test_client.post("/register", json={
        "username": "newuser",
        "email": "test@example.com",  # уже существует
        "password": "123456",
        "full_name": "Дубликат почты"
    })
    assert response.status_code == 400
    assert "Данная электронная почта уже занята" in response.json()["detail"]


def test_login_success(test_client):
    response = test_client.post("/token", data={
        "username": "testuser",
        "password": "123456"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_nonexistent_user(test_client):
    response = test_client.post("/token", data={
        "username": "nonexistentuser",
        "password": "123456"
    })
    assert response.status_code == 401
    assert "Такого пользователя не существует" in response.json()["detail"]


def test_login_wrong_password(test_client):
    response = test_client.post("/token", data={
        "username": "testuser",
        "password": "wrongpassword123"
    })
    assert response.status_code == 401
    assert "Неверный пароль" in response.json()["detail"]


def test_create_admin_by_admin(test_client):
    login = test_client.post("/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]

    response = test_client.post(
        "/register/admin",
        json={
            "username": "superadmin2",
            "email": "super2@club.com",
            "password": "admin",
            "full_name": "Второй Админ"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_create_admin_by_regular_user(test_client):
    login = test_client.post("/token", data={"username": "testuser", "password": "123456"})
    token = login.json()["access_token"]

    response = test_client.post(
        "/register/admin",
        json={"username": "fakeadmin", "email": "fake@club.com", "password": "123", "full_name": "Fake"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403  # Forbidden


def test_create_game_as_admin(test_client):
    login = test_client.post("/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    game_name = "TestGameAdmin"
    response = test_client.post(
        "/games/",
        json={
            "name": game_name,
            "min_players": 3,
            "max_players": 4,
            "duration": 90,
            "category": "strategy",
            "description": "Test game",
            "total_quantity": 2
        },
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == game_name


def test_create_duplicate_game(test_client):
    login = test_client.post("/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.post(
        "/games/",
        json={
            "name": "Catan",
            "min_players": 3,
            "max_players": 4,
            "duration": 90,
            "category": "strategy",
            "description": "Duplicate test",
            "total_quantity": 1
        },
        headers=headers
    )
    assert response.status_code in (400, 409)


def test_reservation_limit(test_client):
    login = test_client.post("/token", data={"username": "testuser", "password": "123456"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    test_client.post("/reservations/", json={"game_name": "Catan"}, headers=headers)

    response = test_client.post("/reservations/", json={"game_name": "Ticket to Ride"}, headers=headers)
    assert response.status_code == 400
    assert "У вас уже есть активная резервация. Верните предыдущую игру." in response.json()["detail"]


def test_return_game_with_rating(test_client):
    login = test_client.post("/token", data={"username": "testuser", "password": "123456"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    test_client.post("/reservations/", json={"game_name": "Catan"}, headers=headers)
    response = test_client.post(
        "/reservations/return",
        json={"duration_rating": "45 min", "rules_simplicity": 4},
        headers=headers
    )
    assert response.status_code == 200


def test_return_game_invalid_rating(test_client):
    login = test_client.post("/token", data={"username": "testuser", "password": "123456"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.post(
        "/reservations/return",
        json={"duration_rating": "invalid_value", "rules_simplicity": 6},
        headers=headers
    )
    assert response.status_code == 422  # Validation error


def test_analytics_popular(test_client):
    login = test_client.post("/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]

    response = test_client.get(
        "/analytics/popular-games",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_analytics_recommendations(test_client):
    login = test_client.post("/token", data={"username": "testuser", "password": "123456"})
    token = login.json()["access_token"]
    response = test_client.get("/analytics/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_purchase_suggestions_only_admin(test_client):
    login = test_client.post("/token", data={"username": "testuser", "password": "123456"})
    token = login.json()["access_token"]
    response = test_client.get("/analytics/purchase-suggestions", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_purchase_suggestions_as_admin(test_client):
    login = test_client.post("/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]

    response = test_client.get(
        "/analytics/purchase-suggestions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_game_success(test_client):
    login = test_client.post("/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    game_name = "GameForUpdateTest"
    test_client.post("/games/", json={
        "name": game_name,
        "min_players": 3,
        "max_players": 4,
        "duration": 90,
        "category": "strategy",
        "description": "Original",
        "total_quantity": 2
    }, headers=headers)

    response = test_client.put(
        f"/games/{game_name}",
        json={
            "name": game_name,
            "min_players": 2,
            "max_players": 6,
            "duration": 150,
            "category": "strategy",
            "description": "Updated successfully",
            "total_quantity": 3
        },
        headers=headers
    )
    assert response.status_code == 200


def test_update_nonexistent_game(test_client):
    login = test_client.post("/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.put(
        "/games/NonExistentGame123",
        json={
            "name": "NonExistentGame123",
            "min_players": 2,
            "max_players": 4,
            "duration": 60,
            "category": "party",
            "description": "Test",
            "total_quantity": 1
        },
        headers=headers
    )
    assert response.status_code == 404


def test_delete_game_success(test_client):
    login = test_client.post("/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    game_name = "GameForDeleteTest"
    test_client.post("/games/", json={
        "name": game_name,
        "min_players": 2,
        "max_players": 4,
        "duration": 60,
        "category": "party",
        "description": "To delete",
        "total_quantity": 1
    }, headers=headers)

    response = test_client.delete(f"/games/{game_name}", headers=headers)
    assert response.status_code == 200


def test_delete_nonexistent_game(test_client):
    login = test_client.post("/token", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.delete("/games/Nonexistent", headers=headers)
    assert response.status_code == 404


def test_regular_user_cannot_create_game(test_client):
    login = test_client.post("/token", data={"username": "testuser", "password": "123456"})
    token = login.json()["access_token"]

    response = test_client.post(
        "/games/",
        json={
            "name": "ForbiddenGame",
            "min_players": 2,
            "max_players": 4,
            "duration": 60,
            "category": "party",
            "description": "Test",
            "total_quantity": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "администратора" in response.json()["detail"]


def test_regular_user_cannot_delete_game(test_client):
    login = test_client.post("/token", data={"username": "testuser", "password": "123456"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    game_name = f"Protected"
    admin_token = test_client.post("/token", data={"username": "admin", "password": "admin"}).json()["access_token"]

    test_client.post("/games/", json={
        "name": game_name,
        "min_players": 3,
        "max_players": 4,
        "duration": 90,
        "category": "strategy",
        "description": "Protected",
        "total_quantity": 1
    }, headers={"Authorization": f"Bearer {admin_token}"})

    response = test_client.delete(f"/games/{game_name}", headers=headers)
    assert response.status_code == 403
