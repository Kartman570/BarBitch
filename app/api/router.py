from fastapi import APIRouter
from .routes_v1 import router as v1_router

api_router = APIRouter()
api_router.include_router(v1_router, prefix="/v1")
