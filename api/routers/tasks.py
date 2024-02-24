from fastapi import APIRouter, HTTPException, status

from api.database import DBDep, findMilestoneById, findProjectById, insertTask
from api.routers.users import UserDep
from api.schemas import CreateableTask, Task

router = APIRouter()


@router.post("/", name="Create Task")
def createTask(createableTask: CreateableTask, db: DBDep, user: UserDep) -> Task:
    if not findProjectById(db, createableTask.projectId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not findMilestoneById(db, createableTask.milestoneId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found",
        )

    if not user.canAccess(createableTask.projectId):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    task = Task(**createableTask.model_dump())
    if not (result := insertTask(db, task)).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )

    task.id = str(result.inserted_id)

    return task
