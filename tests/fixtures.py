import pytest
from pydantic import BaseModel
from Wrappers.models import Base, engine

class User(BaseModel):
    email: str


@pytest.fixture
def fake_user():
    return User(email="cool_guy@gmail.com")


# simply waits until a test is over, and clears database
@pytest.fixture(autouse=True)
def test_db():
    print("Creating schemas...")
    Base.metadata.create_all(bind=engine)
    yield # wait
    print("Deleting schemas...")
    Base.metadata.drop_all(engine)
