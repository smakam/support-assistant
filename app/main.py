from dotenv import load_dotenv
import os
# Load .env from the project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.tracing import setup_langsmith

# Initialize LangSmith tracing
setup_langsmith()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Create feedback directory if it doesn't exist
os.makedirs(settings.FEEDBACK_DIR, exist_ok=True)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Customer Assistant API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    } 