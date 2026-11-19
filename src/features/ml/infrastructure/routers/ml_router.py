from fastapi import APIRouter, Request, status

# Webhook minimal: acepta cualquier notificación de ML y responde 200.
router = APIRouter(prefix="/ml", tags=["ML"])


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook(request: Request):
    return {"received": True}


@router.get("/webhook", status_code=status.HTTP_200_OK)
async def webhook_get():
    return {"ok": True, "service": "ml-webhook"}
