from fastapi import APIRouter, HTTPException, status

from api.database import (
    DBDep,
    findMilestoneAndUpdate,
    findMilestoneById,
    findProjectById,
    findTasks,
    insertMilestone,
    removeMilestone,
    updateManyMilestones,
    updateManyTasks,
)
from api.routers.tasks import deleteTask
from api.routers.users import UserDep
from api.schemas import CreateableMilestone, Milestone, UpdateableMilestone

router = APIRouter()


# FR14
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


# FR23
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


# FR15
@router.patch("/{id}", name="Update Milestone")
def updateMilestone(
    id: str, updateableMilestone: UpdateableMilestone, db: DBDep, user: UserDep
) -> Milestone:
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

    if not (
        result := findMilestoneAndUpdate(
            db, id, {"$set": updateableMilestone.model_dump(exclude_none=True)}
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update milestone",
        )

    return Milestone(**result)


# FR16
@router.delete("/{id}", name="Delete Milestone")
def deleteMilestone(id: str, db: DBDep, user: UserDep):
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

    if not removeMilestone(db, id).deleted_count:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete milestone",
        )

    for task in findTasks(db, {"milestoneId": id}):
        deleteTask(str(task["_id"]), db, user)

    if not updateManyMilestones(
        db,
        {},
        {"$pull": {"dependentMilestones": id}},
    ).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove task from milestone",
        )

    if not updateManyTasks(
        db,
        {},
        {"$pull": {"dependentMilestones": id}},
    ).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove task from dependent tasks",
        )

    return {"message": "Milestone deleted successfully"}
