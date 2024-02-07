from fastapi import APIRouter

from .users import router as usersRouter

router = APIRouter()

router.include_router(usersRouter, prefix="/users", tags=["Users"])
