import os

from fastapi import APIRouter, HTTPException, status
from jose import jwt
from passlib.hash import bcrypt
from pymongo import ReturnDocument
from regex import F

from ..database import usersCollection
from ..schemas import EditableUser, User

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "kraken")

router = APIRouter()


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model_by_alias=False
)
def register(editableUser: EditableUser) -> User:
    editableUser.password = hashPassword(editableUser.password)

    user = User(**editableUser.model_dump())

    if not (
        result := usersCollection.insert_one(user.model_dump(exclude={"id"}))
    ).acknowledged:
        raise HTTPException(status_code=500, detail="Failed to create user")

    userWithToken = usersCollection.find_one_and_update(
        {"_id": result.inserted_id},
        {"$set": {"token": createToken(str(result.inserted_id))}},
        return_document=ReturnDocument.AFTER,
    )

    return User(**userWithToken)


@router.post("/login", response_model_by_alias=False)
def login(username: str, password: str) -> User:
    user = usersCollection.find_one({"username": username})

    if user is None or not verifyPassword(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return User(**user)


def hashPassword(password: str):
    return bcrypt.hash(password)


def createToken(id: str):
    return jwt.encode({"sub": id}, JWT_SECRET_KEY, algorithm="HS256")


def verifyPassword(plainPassword: str, hashedPassword: str):
    return bcrypt.verify(plainPassword, hashedPassword)
