"""Main FastAPI application for Field Intake Service."""

from fastapi import FastAPI

app = FastAPI(title="Field Intake Service")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
