from fastapi import APIRouter

from .projects import router as projectsRouter
from .users import router as usersRouter

router = APIRouter()

router.include_router(usersRouter, prefix="/users", tags=["Users"])
router.include_router(projectsRouter, prefix="/projects", tags=["Projects"])
