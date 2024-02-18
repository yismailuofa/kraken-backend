from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Path, status
from pymongo import ReturnDocument

from api.database import DBDep
from api.routers.users import UserDep
from api.schemas import CreateableProject, Project, User
from api.util import PyObjectId

router = APIRouter()


@router.post("/", name="Create Project")
def createProject(
    createableProject: CreateableProject,
    db: DBDep,
    user: UserDep,
) -> Project:

    project = Project(**createableProject.model_dump())
    if not (
        result := db.projects.insert_one(project.model_dump(exclude={"id"}))
    ).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )

    project.id = str(result.inserted_id)

    if not (
        result := db.users.update_one(
            {"_id": user.oid()}, {"$push": {"ownedProjects": project.id}}
        )
    ).modified_count:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )

    return project


@router.get("/", name="Get Owned & Joined Projects")
def getProjects(db: DBDep, user: UserDep) -> list[Project]:
    return [
        Project(**project)
        for project in db.projects.find(
            {
                "_id": {
                    "$in": [
                        ObjectId(id) for id in user.ownedProjects + user.joinedProjects
                    ]
                }
            }
        )
    ]


@router.get("/{id}", name="Get Project")
def getProject(id: PyObjectId, db: DBDep, user: UserDep) -> Project:
    if str(id) not in user.ownedProjects + user.joinedProjects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    if not (project := db.projects.find_one({"_id": id})):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return Project(**project)


@router.post("/users/add", name="Add User to Project")
def addUserToProject(
    projectId: str,
    username: str,
    db: DBDep,
    user: UserDep,
) -> User:
    if projectId not in user.ownedProjects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not own project",
        )

    if not db.projects.find_one({"_id": ObjectId(projectId)}):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not (
        updatedUser := db.users.find_one_and_update(
            {"username": username},
            {"$addToSet": {"joinedProjects": projectId}},
            return_document=ReturnDocument.AFTER,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return User(**updatedUser)


@router.delete("/users/remove", name="Remove User from Project")
def removeUserFromProject(
    projectId: str,
    username: str,
    db: DBDep,
    user: UserDep,
) -> User:
    if projectId not in user.ownedProjects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not own project",
        )

    if not db.projects.find_one({"_id": ObjectId(projectId)}):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not (
        updatedUser := db.users.find_one_and_update(
            {"username": username},
            {"$pull": {"joinedProjects": projectId}},
            return_document=ReturnDocument.AFTER,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return User(**updatedUser)
