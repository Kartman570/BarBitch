from fastapi import APIRouter
from .new_routes import router as new_router

api_router = APIRouter()
api_router.include_router(new_router, prefix="/v1")
