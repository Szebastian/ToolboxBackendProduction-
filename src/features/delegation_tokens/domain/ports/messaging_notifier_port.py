from abc import ABC, abstractmethod

class IMessagingNotifier(ABC):
    @abstractmethod
    async def send_whatsapp_delegation_link(self, phone: str, mechanic_name: str, direct_url: str) -> None:
        pass

