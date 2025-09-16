#!/usr/bin/env python3
"""
Main entry point for the Ascent Planner Calendar FastAPI application
"""
import uvicorn
from .web import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
