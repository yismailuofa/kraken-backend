from fastapi import APIRouter, HTTPException, status

from api.database import DBDep, findProjectById, insertSprint
from api.routers.users import UserDep
from api.schemas import CreateableSprint, Sprint

router = APIRouter()


@router.post("/", name="Create Sprint")
def createSprint(
    createableSprint: CreateableSprint, db: DBDep, user: UserDep
) -> Sprint:
    if not findProjectById(db, createableSprint.projectId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not user.canAccess(createableSprint.projectId):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    sprint = Sprint(**createableSprint.model_dump())
    if not (result := insertSprint(db, sprint)).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sprint",
        )

    sprint.id = str(result.inserted_id)

    return sprint
