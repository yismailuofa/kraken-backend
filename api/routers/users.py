import os

from fastapi import APIRouter, HTTPException, status
from jose import jwt
from passlib.hash import bcrypt

from ..database import PyObjectId, usersCollection
from ..schemas import EditableUser, User

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "kraken")

router = APIRouter()


def hashPassword(password: str):
    return bcrypt.hash(password)


def createToken(user: EditableUser):
    return jwt.encode({"sub": user.username}, JWT_SECRET_KEY, algorithm="HS256")


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model_by_alias=False
)
def register(editableUser: EditableUser) -> User:
    editableUser.password = hashPassword(editableUser.password)

    user = User(**editableUser.model_dump(), token=createToken(editableUser))

    result = usersCollection.insert_one(user.model_dump(exclude={"id"}))

    if not result.acknowledged:
        raise HTTPException(status_code=500, detail="Failed to create user")

    user.id = str(result.inserted_id)

    return user
