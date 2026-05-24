import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.domain import Base
from app.core.database import get_db
from app.main import app

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/test_db")
    local_engine = create_engine(db_url)
    
    Base.metadata.drop_all(bind=local_engine)
    Base.metadata.create_all(bind=local_engine)
    yield local_engine

@pytest.fixture(scope="function")
def db_session():
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/test_db")
    local_engine = create_engine(db_url)
    
    try:
        Base.metadata.drop_all(bind=local_engine)
        Base.metadata.create_all(bind=local_engine)
    except Exception:
        pass
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=local_engine)
    session = TestingSessionLocal()

    app.dependency_overrides[get_db] = lambda: session

    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.clear()
