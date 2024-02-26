from fastapi import APIRouter, HTTPException, status

from api.database import (
    DBDep,
    findMilestoneById,
    findProjectById,
    findTaskAndUpdate,
    findTaskById,
    insertTask,
    removeTask,
    updateManyMilestones,
    updateManyTasks,
)
from api.routers.users import UserDep
from api.schemas import CreateableTask, Task, UpdateableTask

router = APIRouter()


@router.post("/", name="Create Task")
def createTask(createableTask: CreateableTask, db: DBDep, user: UserDep) -> Task:
    if not findProjectById(db, createableTask.projectId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not (milestone := findMilestoneById(db, createableTask.milestoneId)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found",
        )

    if milestone["projectId"] != createableTask.projectId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Milestone does not belong to project",
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


@router.get("/{id}", name="Get Task")
def getTask(id: str, db: DBDep, user: UserDep) -> Task:
    if not (task := findTaskById(db, id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if not user.canAccess(task["projectId"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    return Task(**task)


@router.patch("/{id}", name="Update Task")
def updateTask(
    id: str, updateableTask: UpdateableTask, db: DBDep, user: UserDep
) -> Task:
    if updateableTask.projectId and not findProjectById(db, updateableTask.projectId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if updateableTask.milestoneId and not findMilestoneById(
        db, updateableTask.milestoneId
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Milestone not found",
        )

    if not (task := findTaskById(db, id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if not user.canAccess(task["projectId"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    setFields = {**updateableTask.model_dump(exclude_none=True)}

    if qaTask := setFields.pop("qaTask", None):
        for k, v in qaTask.items():
            setFields[f"qaTask.{k}"] = v

    if not (result := findTaskAndUpdate(db, id, {"$set": setFields})):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task",
        )

    return Task(**result)


@router.delete("/{id}", name="Delete Task")
def deleteTask(id: str, db: DBDep, user: UserDep):
    if not (task := findTaskById(db, id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if not user.canAccess(task["projectId"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    if not removeTask(db, id).deleted_count:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task",
        )

    if not updateManyMilestones(
        db,
        {},
        {"$pull": {"dependentTasks": id}},
    ).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove task from milestone",
        )

    if not updateManyTasks(
        db,
        {},
        {"$pull": {"dependentTasks": id}},
    ).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove task from dependent tasks",
        )

    return {"message": "Task deleted successfully"}
