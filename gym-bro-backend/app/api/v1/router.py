from fastapi import APIRouter

from app.api.v1 import exercises, export, progress, templates, workouts

router = APIRouter(prefix="/api/v1")
router.include_router(exercises.router)
router.include_router(templates.router)
router.include_router(workouts.router)
router.include_router(progress.router)
router.include_router(export.router)
