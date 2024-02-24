from fastapi import APIRouter

from .milestones import router as milestonesRouter
from .projects import router as projectsRouter
from .tasks import router as tasksRouter
from .users import router as usersRouter

router = APIRouter()

router.include_router(usersRouter, prefix="/users", tags=["Users"])
router.include_router(projectsRouter, prefix="/projects", tags=["Projects"])
router.include_router(milestonesRouter, prefix="/milestones", tags=["Milestones"])
router.include_router(tasksRouter, prefix="/tasks", tags=["Tasks"])
