import pytest
from typing import Generator
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base, get_db
from app.config import settings
from app.models import User, Household
from app.core.security import get_password_hash


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db")
def session_fixture() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_db(db: Session) -> Generator[None, None, None]:
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def create_test_user(db: Session) -> User:
    household = Household(name="Test Household")
    db.add(household)
    db.commit()
    db.refresh(household)

    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        household_id=household.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture()
def auth_client(client: TestClient, create_test_user: User) -> TestClient:
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200

    access_token = response.cookies.get("access_token")
    if access_token:
        client.cookies["access_token"] = access_token

    return client
