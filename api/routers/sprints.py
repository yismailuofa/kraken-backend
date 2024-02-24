from fastapi import APIRouter, HTTPException, status

from api.database import (
    DBDep,
    findProjectById,
    findSprintAndUpdate,
    findSprintById,
    insertSprint,
    removeSprint,
)
from api.routers.users import UserDep
from api.schemas import CreateableSprint, Sprint, UpdateableSprint

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


@router.get("/{id}", name="Get Sprint")
def getSprint(id: str, db: DBDep, user: UserDep) -> Sprint:
    if not (sprint := findSprintById(db, id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    if not user.canAccess(sprint["projectId"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    return Sprint(**sprint)


@router.patch("/{id}", name="Update Sprint")
def updateSprint(
    id: str, updateableSprint: UpdateableSprint, db: DBDep, user: UserDep
) -> Sprint:
    if not (sprint := findSprintById(db, id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    if not user.canAccess(sprint["projectId"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    if not (
        result := findSprintAndUpdate(
            db,
            id,
            {
                "$set": updateableSprint.model_dump(exclude_none=True),
            },
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update sprint",
        )

    return Sprint(**result)


@router.delete("/{id}", name="Delete Sprint")
def deleteSprint(id: str, db: DBDep, user: UserDep):
    if not (sprint := findSprintById(db, id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found",
        )

    if not user.canAccess(sprint["projectId"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    if not removeSprint(db, id).deleted_count:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete sprint",
        )

    return {"message": "Sprint deleted successfully"}
