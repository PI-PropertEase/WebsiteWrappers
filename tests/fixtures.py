import pytest
from pydantic import BaseModel


class User(BaseModel):
    email: str


@pytest.fixture
def fake_user():
    return User(email="cool_guy@gmail.com")
