import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from passlib.hash import bcrypt

from api.database import (
    DBDep,
    findUserAndUpdate,
    findUserByEmail,
    findUserById,
    findUserByUsername,
    insertUser,
)
from api.schemas import CreatableUser, User

router = APIRouter()

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "kraken")


# FR1
@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model_by_alias=False
)
def register(createableUser: CreatableUser, db: DBDep) -> User:
    if findUserByUsername(db, createableUser.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    if findUserByEmail(db, createableUser.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    createableUser.password = hashPassword(createableUser.password)

    user = User(**createableUser.model_dump())

    if not (insertedUserResult := insertUser(db, user)).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    user.id = str(insertedUserResult.inserted_id)

    if not (
        userWithToken := findUserAndUpdate(
            db,
            user,
            {"$set": {"token": createToken(user.id)}},
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )

    return User(**userWithToken)


# FR2
@router.post("/login", response_model_by_alias=False)
def login(username: str, password: str, db: DBDep) -> User:
    if not (user := findUserByUsername(db, username)) or not verifyPassword(
        password, user["password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return User(**user)


# FR2
def getCurrentUser(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(HTTPBearer(description="The user's token")),
    ],
    db: DBDep,
) -> User:
    try:
        token = credentials.credentials

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        if not (user := findUserById(db, payload["sub"])) or user["token"] != token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return User(**user)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


UserDep = Annotated[User, Depends(getCurrentUser)]


# FR2
@router.get("/me", response_model_by_alias=False)
def me(user: UserDep) -> User:
    return user


# FR3
@router.patch("/password/reset", response_model_by_alias=False, name="Reset Password")
def resetPassword(
    newPassword: str,
    db: DBDep,
    user: UserDep,
) -> User:
    if not (
        updatedUser := findUserAndUpdate(
            db, user, {"$set": {"password": hashPassword(newPassword)}}
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    return User(**updatedUser)


# FR3
def hashPassword(password: str):
    return bcrypt.hash(password)


# FR3
def createToken(id: str):
    return jwt.encode({"sub": id}, JWT_SECRET_KEY, algorithm="HS256")


# FR3
def verifyPassword(plainPassword: str, hashedPassword: str):
    return bcrypt.verify(plainPassword, hashedPassword)
