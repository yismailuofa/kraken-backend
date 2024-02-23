from fastapi import APIRouter, HTTPException, status

from api.database import DBDep, findMilestoneById, findProjectById, insertMilestone
from api.routers.users import UserDep
from api.schemas import CreateableMilestone, Milestone

router = APIRouter()


@router.post("/", name="Create Milestone")
def createMilestone(
    createableMilestone: CreateableMilestone, db: DBDep, user: UserDep
) -> Milestone:
    if not findProjectById(db, createableMilestone.projectId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not user.canAccess(createableMilestone.projectId):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    milestone = Milestone(**createableMilestone.model_dump())
    if not (result := insertMilestone(db, milestone)).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create milestone",
        )

    milestone.id = str(result.inserted_id)

    return milestone


@router.get("/{id}", name="Get Milestone")
def getMilestone(id: str, db: DBDep, user: UserDep) -> Milestone:
    if not (milestone := findMilestoneById(db, id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found",
        )

    if not user.canAccess(milestone["projectId"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    return Milestone(**milestone)
