from fastapi import APIRouter
from app.api.v1.endpoints import support

api_router = APIRouter()
api_router.include_router(support.router, prefix="/support", tags=["support"]) 