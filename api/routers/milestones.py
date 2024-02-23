from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from api.database import DBDep
from api.routers.users import UserDep
from api.schemas import CreateableMilestone, Milestone

router = APIRouter()


@router.post("/", name="Create Milestone")
def createMilestone(
    createableMilestone: CreateableMilestone, db: DBDep, user: UserDep
) -> Milestone:
    if not (db.projects.find_one({"_id": ObjectId(createableMilestone.projectId)})):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if createableMilestone.projectId not in user.projects():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    milestone = Milestone(**createableMilestone.model_dump())
    if not (
        result := db.milestones.insert_one(milestone.model_dump(exclude={"id"}))
    ).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create milestone",
        )

    milestone.id = str(result.inserted_id)

    return milestone
