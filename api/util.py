import datetime
import os
from typing import Annotated

from bson import ObjectId
from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from api.database import DBDep
from api.schemas import User

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "kraken")


# This function is a dependency that will be used to convert a string in a request to an ObjectId.
def toObjectId(id: str) -> ObjectId:
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId")
    return ObjectId(id)


PyObjectId = Annotated[ObjectId, Depends(toObjectId)]


def getCurrentUser(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    db: DBDep,
) -> User:
    try:
        token = credentials.credentials

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        userId = ObjectId(payload["sub"])

        if not (user := db.users.find_one({"_id": userId})) or user["token"] != token:
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
