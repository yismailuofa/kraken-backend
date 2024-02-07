from fastapi import APIRouter

from ..database import PyObjectId

router = APIRouter()


@router.get("/")
def read_root() -> dict:
    return {"Hello": "World1"}


@router.get("/{id}")
def read_item(id: PyObjectId):
    return {"id": id.__str__()}
