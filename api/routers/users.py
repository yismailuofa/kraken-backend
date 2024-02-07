from fastapi import APIRouter
from passlib.hash import bcrypt

from ..database import PyObjectId
from ..schemas import EditableUser

router = APIRouter()


def hashPassword(password: str):
    return bcrypt.hash(password)


@router.post("/register")
def register(user: EditableUser):
    user.password = hashPassword(user.password)

    return user.model_dump()
