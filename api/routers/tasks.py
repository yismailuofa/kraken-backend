from fastapi import APIRouter

from api.database import DBDep
from api.routers.users import UserDep
from api.schemas import CreateableTask, Task

router = APIRouter()


@router.post("/", name="Create Task")
def createTask(createableTask: CreateableTask, db: DBDep, user: UserDep) -> Task:
    return Task(**createableTask.model_dump())
