from fastapi import APIRouter, HTTPException, status

from api.database import DBDep, client
from api.routers.users import UserDep
from api.schemas import CreateableProject, Project

router = APIRouter()


@router.post("/", name="Create Project")
def createProject(
    createableProject: CreateableProject,
    db: DBDep,
    user: UserDep,
) -> Project:

    project = Project(**createableProject.model_dump())

    result = db.projects.insert_one(project.model_dump(exclude={"id"}))
    if not result.acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )
    project.id = str(result.inserted_id)

    result = db.users.update_one(
        {"_id": user.oid()}, {"$push": {"ownedProjects": project.id}}
    )
    if not result.modified_count:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )

    return project
