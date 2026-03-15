import os
from fastapi import APIRouter
from db.session import check_db_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    environment = os.environ.get("ENVIRONMENT", "development")
    db_status = await check_db_connection()

    return {
        "status": "healthy",
        "service": "careorbit-api",
        "version": "0.3.0",
        "environment": environment,
        "database": db_status,
    }
