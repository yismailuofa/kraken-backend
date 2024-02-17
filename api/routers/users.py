from fastapi import APIRouter, HTTPException, status
from jose import jwt
from passlib.hash import bcrypt
from pymongo import ReturnDocument

from api.database import DBDep
from api.schemas import EditableUser, User
from api.util import JWT_SECRET_KEY, UserDep

router = APIRouter()


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model_by_alias=False
)
def register(editableUser: EditableUser, db: DBDep) -> User:
    if db.users.find_one({"username": editableUser.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    editableUser.password = hashPassword(editableUser.password)

    user = User(**editableUser.model_dump())

    if not (
        insertedUserResult := db.users.insert_one(user.model_dump(exclude={"id"}))
    ).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    if not (
        userWithToken := db.users.find_one_and_update(
            {"_id": insertedUserResult.inserted_id},
            {"$set": {"token": createToken(str(insertedUserResult.inserted_id))}},
            return_document=ReturnDocument.AFTER,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    return User(**userWithToken)


@router.post("/login", response_model_by_alias=False)
def login(username: str, password: str, db: DBDep) -> User:
    if not (user := db.users.find_one({"username": username})) or not verifyPassword(
        password, user["password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return User(**user)


@router.get("/me", response_model_by_alias=False)
def me(user: UserDep) -> User:
    return user


@router.put("/password/reset", response_model_by_alias=False, name="Reset Password")
def resetPassword(
    newPassword: str,
    db: DBDep,
    user: UserDep,
) -> User:
    if not (
        updatedUser := db.users.find_one_and_update(
            {"_id": user.oid()},
            {"$set": {"password": hashPassword(newPassword)}},
            return_document=ReturnDocument.AFTER,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    return User(**updatedUser)


def hashPassword(password: str):
    return bcrypt.hash(password)


def createToken(id: str):
    return jwt.encode({"sub": id}, JWT_SECRET_KEY, algorithm="HS256")


def verifyPassword(plainPassword: str, hashedPassword: str):
    return bcrypt.verify(plainPassword, hashedPassword)
