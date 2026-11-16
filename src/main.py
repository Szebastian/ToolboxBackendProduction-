from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv

from src.features.delegation_tokens.infrastructure.routers.delegation_router import router as delegation_router
from src.features.vehicles.infrastructure.routers.vehicle_router import router as vehicle_router
from src.features.parts_request.infrastructure.routers.parts_request_router import router as parts_request_router
from src.features.vendor_quoting.infrastructure.routers.vendor_quoting_router import router as vendor_quoting_router
from src.features.orders.infrastructure.routers.order_router import router as order_router
from src.features.catalog.infrastructure.routers.catalog_router import router as catalog_router
from src.features.uploads.infrastructure.routers.upload_router import router as upload_router
from src.features.mechanics.infrastructure.routers.mechanic_router import router as mechanic_router
from src.features.cedula_extraccion.infrastructure.routers.cedula_router import router as cedula_router
from src.features.auth_registro.infrastructure.routers.auth_router import router as auth_router

load_dotenv()

app = FastAPI(
    title="Toolbox Backend API",
    description="API RESTful en Python (FastAPI) para el Marketplace Hiperlocal de Autopartes Toolbox",
    version="1.0.0"
)

# Configuración de CORS: orígenes explícitos desde CORS_ORIGINS (separados por coma).
# Nunca "*" con credentials: el navegador lo rechaza y deja la API abierta a cualquier sitio.
_origins = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
]
if os.getenv("FRONTEND_URL"):
    _origins.append(os.getenv("FRONTEND_URL").strip())
if not _origins:
    _origins = [
        "http://localhost:4300",
        "http://127.0.0.1:4300",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)


@app.middleware("http")
async def private_network_access(request, call_next):
    """Preflight extra que Chrome exige para sitios públicos que golpean un
    backend privado (ej: la web publicada en Netlify probando contra este
    backend corriendo en localhost). Sin esto, el navegador cancela la llamada
    aunque el CORS esté bien configurado."""
    respuesta = await call_next(request)
    if request.headers.get("access-control-request-private-network"):
        respuesta.headers["Access-Control-Allow-Private-Network"] = "true"
    return respuesta

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
app.include_router(order_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(mechanic_router, prefix="/api/v1")
app.include_router(cedula_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
