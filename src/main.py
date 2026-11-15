from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv

from src.features.delegation_tokens.infrastructure.routers.delegation_router import router as delegation_router
from src.features.vehicles.infrastructure.routers.vehicle_router import router as vehicle_router
from src.features.parts_request.infrastructure.routers.parts_request_router import router as parts_request_router
from src.features.vendor_quoting.infrastructure.routers.vendor_quoting_router import router as vendor_quoting_router

load_dotenv()

app = FastAPI(
    title="Toolbox Backend API",
    description="API RESTful en Python (FastAPI) para el Marketplace Hiperlocal de Autopartes Toolbox",
    version="1.0.0"
)

# Configuración de CORS
origins = [
    "http://localhost:4300",
    "http://127.0.0.1:4300",
    os.getenv("FRONTEND_URL", "http://localhost:4300"),
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck para Render
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "toolbox-backend-api-python"
    }

# Montar Routers de cada Vertical Slice bajo /api/v1
app.include_router(delegation_router, prefix="/api/v1")
app.include_router(vehicle_router, prefix="/api/v1")
app.include_router(parts_request_router, prefix="/api/v1")
app.include_router(vendor_quoting_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
