from fastapi import APIRouter

from .clients import router as clients_router
from .items import router as items_router
from .orders import router as orders_router

api_router = APIRouter()

api_router.include_router(clients_router, prefix="/clients", tags=["clients"])
api_router.include_router(items_router, prefix="/items", tags=["items"])
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])
