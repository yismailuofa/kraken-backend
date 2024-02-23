from fastapi import APIRouter, HTTPException, status

from api.database import (
    DBDep,
    findProjectAndUpdate,
    findProjectById,
    findUserAndUpdate,
    findUserAndUpdateByEmail,
    findUserAndUpdateById,
    insertProject,
    toObjectId,
)
from api.routers.users import UserDep
from api.schemas import CreateableProject, Project, UpdateableProject, User, UserView

router = APIRouter()


@router.post("/", name="Create Project")
def createProject(
    createableProject: CreateableProject,
    db: DBDep,
    user: UserDep,
) -> Project:

    project = Project(**createableProject.model_dump())
    if not (result := insertProject(db, project)).acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )

    project.id = str(result.inserted_id)

    if not findUserAndUpdate(
        db,
        user,
        {"$push": {"ownedProjects": project.id}},
    ):
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
            {"_id": {"$in": [toObjectId(id) for id in user.projects()]}}
        )
    ]


@router.get("/{id}", name="Get Project")
def getProject(id: str, db: DBDep, user: UserDep) -> Project:
    if not user.canAccess(id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    if not (project := findProjectById(db, id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return Project(**project)


@router.patch("/{id}", name="Update Project")
def updateProject(
    id: str, updateableProject: UpdateableProject, db: DBDep, user: UserDep
) -> Project:
    if not user.isAdmin(id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    if not findProjectById(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not (
        result := findProjectAndUpdate(
            db,
            id,
            {"$set": updateableProject.model_dump(exclude_none=True)},
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project",
        )

    return Project(**result)


@router.post("/{id}/join", name="Join Project")
def joinProject(id: str, db: DBDep, user: UserDep) -> User:
    if not findProjectById(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not (
        updatedUser := findUserAndUpdate(
            db,
            user,
            {"$push": {"joinedProjects": id}},
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join project",
        )

    return User(**updatedUser)


@router.delete("/{id}/leave", name="Leave Project")
def leaveProject(id: str, db: DBDep, user: UserDep) -> User:
    if not findProjectById(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not (
        updatedUser := findUserAndUpdate(
            db,
            user,
            {"$pull": {"joinedProjects": id}},
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave project",
        )

    return User(**updatedUser)


@router.post("/{id}/users", name="Add User to Project")
def addProjectUser(id: str, email: str, user: UserDep, db: DBDep) -> UserView:
    if not user.isAdmin(id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    if not findProjectById(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not (
        updatedUser := findUserAndUpdateByEmail(
            db,
            email,
            {"$push": {"joinedProjects": id}},
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add user to project",
        )

    return UserView(**updatedUser)


@router.delete("/{id}/users", name="Remove User from Project")
def removeProjectUser(id: str, userID: str, user: UserDep, db: DBDep) -> UserView:
    if not user.isAdmin(id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    if not findProjectById(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not (
        updatedUser := findUserAndUpdateById(
            db,
            userID,
            {"$pull": {"joinedProjects": id}},
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove user from project",
        )

    return UserView(**updatedUser)


@router.get("/{id}/users", name="Get Project Users")
def getProjectUsers(id: str, db: DBDep, user: UserDep) -> list[UserView]:
    if not user.isAdmin(id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to project",
        )

    if not findProjectById(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return [UserView(**user) for user in db.users.find({"joinedProjects": id})]
