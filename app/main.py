from fastapi import FastAPI

from app.api.v1 import v1_router
from app.core.config import settings


# from app.api.v2 import v2_router  # You would import v2 here later

def create_app() -> FastAPI:
    """
    Application factory pattern. 
    This is best practice for testing and scalability.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="My scalable FastAPI backend template."
    )

    # Attach the v1 router to the main app, with a base prefix
    app.include_router(v1_router, prefix="/api/v1")
    
    # If you had v2, you would attach it like this:
    # app.include_router(v2_router, prefix="/api/v2")

    return app

# Initialize the application
app = create_app()

@app.get("/health", tags=["System"])
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}