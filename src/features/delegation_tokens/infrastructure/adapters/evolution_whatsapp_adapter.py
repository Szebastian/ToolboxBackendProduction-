import httpx
from typing import Optional
from ...domain.ports.messaging_notifier_port import IMessagingNotifier

class EvolutionWhatsAppAdapter(IMessagingNotifier):
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint = endpoint
        self.api_key = api_key

    async def send_whatsapp_delegation_link(self, phone: str, mechanic_name: str, direct_url: str) -> None:
        message = (
            f"Hola {mechanic_name}! Un cliente te ha delegado la especificación de repuestos "
            f"para su vehículo en Toolbox.\n\nAccedé directamente sin login ni registro aquí:\n"
            f"{direct_url}\n\nEste enlace tiene validez limitada."
        )

        if not self.endpoint or not self.api_key:
            print(f"[WHATSAPP MOCK SIMULATOR] To: {phone}\nMessage: {message}")
            return

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.endpoint}/message/sendText",
                    headers={"apikey": self.api_key, "Content-Type": "application/json"},
                    json={"number": phone, "text": message},
                    timeout=5.0
                )
        except Exception as e:
            print(f"[Evolution WhatsApp Error] {e}")

