from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Smart Waste Collection Travel-Time & Route Simulator (Phase 1 Foundation)",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global structured exception handler to ensure standard API error envelopes."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred.",
            "path": request.url.path,
        },
    )


# Include API router with prefix
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.websocket("/ws/realtime")
async def websocket_realtime_endpoint(websocket: WebSocket):
    """Real-time WebSocket telemetry and alert broadcast stream."""
    from app.telemetry.stream import stream_manager
    from app.telemetry.service import telemetry_service
    await stream_manager.connect(websocket)
    try:
        # Send initial state snapshot immediately
        fused = telemetry_service.get_realtime_state()
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "data": fused.model_dump(),
        })
        while True:
            # Keep-alive / receive client commands (e.g. ping)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await stream_manager.disconnect(websocket)
    except Exception:
        await stream_manager.disconnect(websocket)


@app.get("/")
def root():
    return {
        "message": "Smart Waste Collection Travel-Time & Route Simulator API",
        "phase": settings.PHASE,
        "docs": f"{settings.API_PREFIX}/docs",
        "health": f"{settings.API_PREFIX}/health",
        "websocket": "/ws/realtime",
    }
